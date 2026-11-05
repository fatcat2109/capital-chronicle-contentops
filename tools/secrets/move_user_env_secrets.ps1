<#
.SYNOPSIS
  CC-297: move named user environment variables into Windows Credential Manager, or delete them.

.DESCRIPTION
  -Move NAME[,NAME...]    For each variable in your user environment (HKCU\Environment): store it as the
                          generic credential CapitalChronicle/<NAME> (user name <NAME>, UTF-16LE as the
                          Windows dialog stores it), read it back, and only then delete the variable.
  -Delete NAME[,NAME...]  Delete each variable from your user environment without storing it.
  -DryRun                 Show what would happen; change nothing.

  A name may end in * (for example BINGX_*) to take every user variable whose name starts with it.
  The script prints names and OK, SKIP, NOTE or FAIL only, never a value. It changes only your user
  environment and your own Credential Manager. If Credential Manager already holds a different value
  for a name, nothing changes for that name.

  Programs that are already running keep the values they started with; sign out and back in (or
  restart the PC) afterwards so that none of them keeps an old copy.

.EXAMPLE
  pwsh -NoProfile -File tools\secrets\move_user_env_secrets.ps1 -Move THREADS_APP_SECRET,THREADS_USER_ACCESS_TOKEN
.EXAMPLE
  pwsh -NoProfile -File tools\secrets\move_user_env_secrets.ps1 -Delete BINGX_*,TASTYTRADE_* -DryRun
#>
[CmdletBinding()]
param(
  [string[]] $Move = @(),
  [string[]] $Delete = @(),
  [switch] $DryRun
)
Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'

$TargetPrefix = 'CapitalChronicle/'
$MaxBlobBytes = 2560   # CRED_MAX_CREDENTIAL_BLOB_SIZE
$ErrorNotFound = 1168

if (-not ('Cc297CredentialStore' -as [type])) {
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class Cc297CredentialStore
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct CREDENTIAL
    {
        public uint Flags;
        public uint Type;
        public string TargetName;
        public string Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public uint CredentialBlobSize;
        public IntPtr CredentialBlob;
        public uint Persist;
        public uint AttributeCount;
        public IntPtr Attributes;
        public string TargetAlias;
        public string UserName;
    }

    [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredRead(string target, uint type, uint flags, out IntPtr credential);

    [DllImport("advapi32.dll", EntryPoint = "CredWriteW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredWrite(ref CREDENTIAL credential, uint flags);

    [DllImport("advapi32.dll", EntryPoint = "CredDeleteW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CredDelete(string target, uint type, uint flags);

    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern void CredFree(IntPtr buffer);

    [DllImport("user32.dll", EntryPoint = "SendMessageTimeoutW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr SendMessageTimeout(IntPtr window, uint message, UIntPtr wParam, string lParam,
        uint flags, uint timeout, out UIntPtr result);

    // 0 when found (blob filled), else the Win32 error (1168 = not found).
    public static int Read(string target, out byte[] blob)
    {
        blob = null;
        IntPtr pointer;
        if (!CredRead(target, 1, 0, out pointer)) { return Marshal.GetLastWin32Error(); }
        try
        {
            CREDENTIAL credential = (CREDENTIAL)Marshal.PtrToStructure(pointer, typeof(CREDENTIAL));
            blob = new byte[credential.CredentialBlobSize];
            if (credential.CredentialBlobSize > 0)
            {
                Marshal.Copy(credential.CredentialBlob, blob, 0, (int)credential.CredentialBlobSize);
            }
            return 0;
        }
        finally { CredFree(pointer); }
    }

    // A generic credential persisted on this machine for this user; 0 on success, else the Win32 error.
    public static int Write(string target, string userName, byte[] blob, string comment)
    {
        CREDENTIAL credential = new CREDENTIAL();
        credential.Type = 1;
        credential.TargetName = target;
        credential.UserName = userName;
        credential.Comment = comment;
        credential.Persist = 2;
        credential.CredentialBlobSize = (uint)blob.Length;
        credential.CredentialBlob = Marshal.AllocHGlobal(Math.Max(blob.Length, 1));
        try
        {
            Marshal.Copy(blob, 0, credential.CredentialBlob, blob.Length);
            if (!CredWrite(ref credential, 0)) { return Marshal.GetLastWin32Error(); }
            return 0;
        }
        finally
        {
            for (int i = 0; i < blob.Length; i++) { Marshal.WriteByte(credential.CredentialBlob, i, 0); }
            Marshal.FreeHGlobal(credential.CredentialBlob);
        }
    }

    public static int Delete(string target)
    {
        if (!CredDelete(target, 1, 0)) { return Marshal.GetLastWin32Error(); }
        return 0;
    }

    // Tell Explorer and other windows that the user environment changed (as the Windows dialog does).
    public static void BroadcastEnvironmentChange()
    {
        UIntPtr ignored;
        SendMessageTimeout(new IntPtr(0xffff), 0x001A, UIntPtr.Zero, "Environment", 0x0002, 5000, out ignored);
    }
}
'@
}

function Say([string] $state, [string] $name, [string] $text) {
  # Straight to the console, so no line can end up in a function's return value.
  [Console]::Out.WriteLine(('{0,-5} {1}  {2}' -f $state, $name, $text))
}

function Split-Names([string[]] $values) {
  @($values | ForEach-Object { $_ -split '[,;\s]+' } | Where-Object { $_ })
}

function Same-Blob([byte[]] $a, [byte[]] $b) {
  if ($null -eq $a -or $null -eq $b -or $a.Length -ne $b.Length) { return $false }
  for ($i = 0; $i -lt $a.Length; $i++) { if ($a[$i] -ne $b[$i]) { return $false } }
  return $true
}

function Clear-Bytes([byte[]] $bytes) {
  if ($null -ne $bytes) { [Array]::Clear($bytes, 0, $bytes.Length) }
}

if (-not @(Split-Names $Move).Count -and -not @(Split-Names $Delete).Count) {
  [Console]::Out.WriteLine('Nothing to do: give names with -Move and/or -Delete (see the help at the top of this file).')
  exit 2
}
$envKey = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', (-not $DryRun))
if ($null -eq $envKey) { [Console]::Out.WriteLine('FAIL  HKCU\Environment could not be opened'); exit 1 }
$userNames = @($envKey.GetValueNames())

function Resolve-Names([string[]] $requested, [string] $verb) {
  $resolved = New-Object System.Collections.Generic.List[string]
  foreach ($item in (Split-Names $requested)) {
    if ($item -notmatch '^[A-Za-z_][A-Za-z0-9_]*\*?$') { Say 'FAIL' $item 'is not a variable name (letters, digits and _ only; * only at the end)'; $script:failed++; continue }
    if ($item.EndsWith('*')) {
      $hits = @($userNames | Where-Object { $_ -like $item } | Sort-Object)
      if (-not $hits.Count) { Say 'SKIP' $item "no user variable matches"; $script:skipped++; continue }
      foreach ($hit in $hits) { if (-not $resolved.Contains($hit)) { $resolved.Add($hit) } }
    } else {
      $exact = @($userNames | Where-Object { $_ -ieq $item }) | Select-Object -First 1
      $name = if ($exact) { [string]$exact } else { $item }
      if (-not $resolved.Contains($name)) { $resolved.Add($name) }
    }
  }
  return ,$resolved
}

$script:moved = 0; $script:deleted = 0; $script:skipped = 0; $script:failed = 0; $changed = $false
$moveNames = Resolve-Names $Move 'move'
$deleteNames = Resolve-Names $Delete 'delete'
foreach ($name in @($moveNames)) {
  if (@($deleteNames | Where-Object { $_ -ieq $name }).Count) {
    Say 'FAIL' $name 'is named in both -Move and -Delete; nothing changed for it'
    $script:failed++
    $moveNames.Remove($name) | Out-Null
    $deleteNames.Remove(($deleteNames | Where-Object { $_ -ieq $name } | Select-Object -First 1)) | Out-Null
  }
}

function Read-UserValue([string] $name) {
  # The variable's text as programs see it, or $null when it is not in the user environment.
  if (-not ($userNames -icontains $name)) { return $null }
  $kind = $envKey.GetValueKind($name)
  $raw = $envKey.GetValue($name, $null, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
  if ($kind -eq [Microsoft.Win32.RegistryValueKind]::ExpandString -and $raw -is [string] -and $raw.Contains('%')) {
    $raw = [Environment]::ExpandEnvironmentVariables($raw)
  }
  if ($kind -ne [Microsoft.Win32.RegistryValueKind]::String -and $kind -ne [Microsoft.Win32.RegistryValueKind]::ExpandString) {
    throw [System.InvalidOperationException]::new('NOT_TEXT')
  }
  return [string]$raw
}

function Remove-UserValue([string] $name) {
  $envKey.DeleteValue($name, $false)
  if ($null -ne $envKey.GetValue($name, $null)) { throw [System.InvalidOperationException]::new('DELETE_NOT_CONFIRMED') }
}

function Note-Machine([string] $name) {
  if ($null -ne [Environment]::GetEnvironmentVariable($name, 'Machine')) {
    Say 'NOTE' $name 'is also set for all users (System variables); this script leaves that one'
  }
}

foreach ($name in $moveNames) {
  $target = $TargetPrefix + $name
  $value = $null; $blob = $null; $stored = $null
  try {
    $value = Read-UserValue $name
    $code = [Cc297CredentialStore]::Read($target, [ref]$stored)
    if ($code -ne 0 -and $code -ne $ErrorNotFound) { Say 'FAIL' $name "Credential Manager could not be read (error $code); nothing changed"; $script:failed++; continue }
    if ($null -eq $value -or $value -eq '') {
      if ($code -eq 0) { Say 'OK' $name "already in Credential Manager ($target); not in your user environment"; $script:moved++ }
      else { Say 'SKIP' $name 'not in your user environment'; $script:skipped++ }
      Note-Machine $name
      continue
    }
    $blob = [System.Text.Encoding]::Unicode.GetBytes($value)
    if ($blob.Length -gt $MaxBlobBytes) { Clear-Bytes $blob; $blob = [System.Text.Encoding]::UTF8.GetBytes($value) }
    if ($blob.Length -gt $MaxBlobBytes) { Say 'FAIL' $name "is longer than Credential Manager allows ($MaxBlobBytes bytes); nothing changed"; $script:failed++; continue }
    if ($code -eq 0) {
      $sameUtf16 = Same-Blob $stored ([System.Text.Encoding]::Unicode.GetBytes($value))
      $sameUtf8 = Same-Blob $stored ([System.Text.Encoding]::UTF8.GetBytes($value))
      if (-not ($sameUtf16 -or $sameUtf8)) {
        Say 'FAIL' $name "Credential Manager already holds a different value for $target; nothing changed. If the stored one is the newer value, run again with -Delete $name"
        $script:failed++; continue
      }
      if ($DryRun) { Say 'OK' $name 'would delete the user variable (Credential Manager already holds the same value)'; $script:moved++; continue }
      Remove-UserValue $name; $changed = $true
      Say 'OK' $name "deleted from your user environment (Credential Manager already held the same value)"
      $script:moved++; Note-Machine $name; continue
    }
    if ($DryRun) { Say 'OK' $name "would move to Credential Manager ($target)"; $script:moved++; continue }
    $code = [Cc297CredentialStore]::Write($target, $name, $blob, 'Moved from the user environment by move_user_env_secrets.ps1 (CC-297)')
    if ($code -ne 0) { Say 'FAIL' $name "Credential Manager refused the write (error $code); the user variable was kept"; $script:failed++; continue }
    $check = $null
    $code = [Cc297CredentialStore]::Read($target, [ref]$check)
    $same = ($code -eq 0) -and (Same-Blob $check $blob)
    Clear-Bytes $check
    if (-not $same) {
      [void][Cc297CredentialStore]::Delete($target)
      Say 'FAIL' $name 'the stored value did not read back the same; removed it and kept the user variable'
      $script:failed++; continue
    }
    Remove-UserValue $name; $changed = $true
    Say 'OK' $name "moved to Credential Manager ($target) and deleted from your user environment"
    $script:moved++; Note-Machine $name
  } catch {
    Say 'FAIL' $name "stopped ($($_.Exception.GetType().Name)$(if ($_.Exception.Message -in @('NOT_TEXT', 'DELETE_NOT_CONFIRMED')) { ': ' + $_.Exception.Message })); check this name by hand"
    $script:failed++
  } finally {
    Clear-Bytes $blob; Clear-Bytes $stored; $value = $null
  }
}

foreach ($name in $deleteNames) {
  try {
    if (-not ($userNames -icontains $name)) { Say 'SKIP' $name 'not in your user environment'; $script:skipped++; Note-Machine $name; continue }
    if ($DryRun) { Say 'OK' $name 'would delete from your user environment (not stored anywhere)'; $script:deleted++; continue }
    Remove-UserValue $name; $changed = $true
    Say 'OK' $name 'deleted from your user environment (not stored anywhere)'
    $script:deleted++; Note-Machine $name
  } catch {
    Say 'FAIL' $name "stopped ($($_.Exception.GetType().Name)); check this name by hand"
    $script:failed++
  }
}

if ($changed) { [Cc297CredentialStore]::BroadcastEnvironmentChange() }
$envKey.Close()
$mode = if ($DryRun) { 'Dry run, nothing changed. ' } else { '' }
[Console]::Out.WriteLine(("{0}Moved {1}, deleted {2}, skipped {3}, failed {4}." -f $mode, $script:moved, $script:deleted, $script:skipped, $script:failed))
if ($changed) { [Console]::Out.WriteLine('Programs already running keep their old copies until they restart: sign out and back in, or restart the PC.') }
if ($script:failed) { exit 1 }
exit 0

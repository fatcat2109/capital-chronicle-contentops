import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';

function openView() {
  render(createElement(App));
  const navBtn = document.getElementById('nav-v6_command_center');
  if (!navBtn) throw new Error('V6 command center nav button not found');
  fireEvent.click(navBtn);
}

describe('V6 Unified Operator Reporting Console Interactive Controls', () => {
  it('toggles scheduler status', () => {
    openView();
    expect(screen.getByText(/Scheduler:\s*Active/i)).toBeInTheDocument();
    
    const toggleBtn = document.getElementById('toggle-scheduler-btn');
    if (!toggleBtn) throw new Error('Toggle scheduler button not found');
    
    // Pause scheduler
    fireEvent.click(toggleBtn);
    expect(screen.getByText(/Scheduler:\s*Paused/i)).toBeInTheDocument();
    
    // Resume scheduler
    fireEvent.click(toggleBtn);
    expect(screen.getByText(/Scheduler:\s*Active/i)).toBeInTheDocument();
  });

  it('runs tick reconciliation and adds mock logs', () => {
    openView();
    expect(screen.getByText(/Run Tick \(0 executed\)/i)).toBeInTheDocument();

    const tickBtn = document.getElementById('run-tick-btn');
    if (!tickBtn) throw new Error('Run tick button not found');

    fireEvent.click(tickBtn);
    expect(screen.getByText(/Run Tick \(1 executed\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Mock active cron tick comments auto-responder/i)).toBeInTheDocument();

    fireEvent.click(tickBtn);
    expect(screen.getByText(/Run Tick \(2 executed\)/i)).toBeInTheDocument();
  });

  it('simulates dispatcher with custom outcomes', () => {
    openView();
    const simBtn = document.getElementById('simulate-dispatch-btn');
    if (!simBtn) throw new Error('Simulate dispatch button not found');

    // Simulate standard success on Facebook Page
    fireEvent.change(document.getElementById('sim-platform-select')!, { target: { value: 'facebook_page' } });
    fireEvent.change(document.getElementById('sim-outcome-select')!, { target: { value: 'success' } });
    fireEvent.click(simBtn);

    expect(screen.getByText(/Simulated post on facebook_page with outcome: success/i)).toBeInTheDocument();

    // Simulate failure with permission_missing classification
    fireEvent.change(document.getElementById('sim-platform-select')!, { target: { value: 'instagram' } });
    fireEvent.change(document.getElementById('sim-outcome-select')!, { target: { value: 'permission_missing' } });
    fireEvent.click(simBtn);

    expect(screen.getByText(/Simulated post on instagram with outcome: permission_missing/i)).toBeInTheDocument();
    expect(screen.getByText(/diagnostic:\s*permission_missing/i)).toBeInTheDocument();
  });

  it('clears execution logs', () => {
    openView();
    const clearBtn = document.getElementById('clear-logs-btn');
    if (!clearBtn) throw new Error('Clear logs button not found');

    // Initially has logs
    expect(screen.getByText(/Scheduled Facebook post\.\.\./i)).toBeInTheDocument();

    fireEvent.click(clearBtn);
    expect(screen.getByText(/No execution logs recorded\./i)).toBeInTheDocument();
  });

  it('renders active queues visualizer', () => {
    openView();
    expect(screen.getByText('Active Queues Visualizer')).toBeInTheDocument();
    expect(screen.getByText('Draft Staging Queue')).toBeInTheDocument();
    expect(screen.getByText('Approval Outbox Queue')).toBeInTheDocument();
    expect(screen.getByText('Scheduler Queue')).toBeInTheDocument();
    expect(screen.getByText('Manual Retry Backlog')).toBeInTheDocument();
  });
});

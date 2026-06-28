const UNSAFE_PATTERNS = [
  "webhook",
  "discord.com/api/webhooks",
  "token",
  "cookie",
  "authorization",
  "bearer",
  ".env",
  "secret",
  "password",
  "pkey",
  "private_key",
  "session",
  "localstorage",
  "sessionstorage",
  "header",
  "appdata",
  "temp"
];

const FINANCIAL_ADVICE = [
  "buy",
  "sell",
  "hold",
  "price target",
  "position sizing",
  "guaranteed prediction",
  "trading signal"
];

document.getElementById('btn-validate').addEventListener('click', (e) => {
  e.preventDefault();
  
  const form = document.getElementById('evidence-form');
  const fields = [
    'operator_idea_source_ref',
    'topic_statement',
    'factual_claims',
    'source_notes',
    'citation_candidates',
    'supporting_artifacts',
    'limitation_notes',
    'no_signal_disclosure',
    'intended_content_lane',
    'intended_canonical_article_angle'
  ];
  
  let validationErrors = [];
  let isComplete = true;
  let hasUnsafe = false;
  let hasFinancialAdvice = false;
  
  fields.forEach(field => {
    const element = document.getElementById(field);
    const val = element ? element.value.trim() : '';
    
    // Check empty or placeholder
    if (!val || val.toLowerCase().includes('placeholder') || val.toLowerCase().includes('replace_')) {
      validationErrors.push(`Field '${field}' is empty or contains placeholders.`);
      isComplete = false;
    }
    
    // Check unsafe
    const valLower = val.toLowerCase();
    for (const pattern of UNSAFE_PATTERNS) {
      if (valLower.includes(pattern)) {
        validationErrors.push(`Field '${field}' contains restricted keyword/pattern: "${pattern}".`);
        hasUnsafe = true;
      }
    }
    
    // Check financial advice
    for (const phrase of FINANCIAL_ADVICE) {
      if (valLower.includes(phrase)) {
        validationErrors.push(`Field '${field}' contains prohibited financial advice term: "${phrase}".`);
        hasFinancialAdvice = true;
      }
    }
  });
  
  const outputDiv = document.getElementById('validation-output');
  outputDiv.className = 'validation-output';
  
  if (hasUnsafe) {
    outputDiv.classList.add('error');
    outputDiv.innerText = `STATUS: FIXTURE_REJECTED_UNSAFE_VALUES\n\nErrors:\n- ${validationErrors.join('\n- ')}`;
  } else if (!isComplete) {
    outputDiv.classList.add('error');
    outputDiv.innerText = `STATUS: FIXTURE_INCOMPLETE_MISSING_SLOTS\n\nErrors:\n- ${validationErrors.join('\n- ')}`;
  } else if (hasFinancialAdvice) {
    outputDiv.classList.add('error');
    outputDiv.innerText = `STATUS: FIXTURE_REJECTED_FINANCIAL_ADVICE\n\nErrors:\n- ${validationErrors.join('\n- ')}`;
  } else {
    outputDiv.classList.add('success');
    outputDiv.innerText = `STATUS: VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW\n\nAll slots checked. No restricted keywords, placeholders, or financial terms detected. Proceed with command-line validation and source submission bridge refresh!`;
  }
});

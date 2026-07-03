import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { createElement } from 'react';
import App from '../App';

function openView() {
  render(createElement(App));
  fireEvent.click(document.getElementById('nav-final_product_readiness')!);
}

describe('Final Product Readiness UI', () => {
  it('renders final readiness summary without live actions', () => {
    openView();

    expect(screen.getAllByText(/Final Product Readiness/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('FINAL_PRODUCT_READY_FOR_LOCAL_OPERATOR_REVIEW_ONLY').length).toBeGreaterThan(0);
    expect(screen.getByText('TASK_0057 evidence')).toBeInTheDocument();
    expect(screen.getByText('safe audit pending')).toBeInTheDocument();
    expect(screen.getByText('dispatch_allowed_now=false')).toBeInTheDocument();
  });

  it('renders operator decision facts as read-only evidence', () => {
    openView();

    expect(screen.getByText('Operator Decision')).toBeInTheDocument();
    expect(screen.getByText('Ready for local operator review only')).toBeInTheDocument();
    expect(screen.getByText('Substack live publish accepted by committed evidence')).toBeInTheDocument();
    expect(screen.getByText('Public URL not verified')).toBeInTheDocument();
    expect(screen.getByText('Dispatch/live write locked')).toBeInTheDocument();
    expect(screen.getByText('Browser/CDP/network/env/credential action not performed')).toBeInTheDocument();
  });

  it('proves unsafe actions stay disabled', () => {
    openView();

    const disabled = screen.getByRole('button', { name: /Publish \/ Dispatch \/ Verify public URL/i });
    expect(disabled).toBeDisabled();
    for (const button of screen.getAllByRole('button').filter((b) => !(b as HTMLButtonElement).disabled)) {
      expect(button.textContent ?? '').not.toMatch(/publish now|post now|send now|schedule now|dispatch live|verify credentials|verify public url/i);
    }
  });
});

import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '../components/layout/Sidebar';
import { Breadcrumbs } from '../components/layout/Breadcrumbs';

describe('Layout & Navigation Components', () => {
  it('renders Sidebar with major platform navigation links', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Sidebar dbStatus="healthy" isBackendOnline={true} />
      </MemoryRouter>
    );

    expect(screen.getByText('WorkforceIQ')).toBeDefined();
    expect(screen.getByText('Executive Dashboard')).toBeDefined();
    expect(screen.getByText('Employee Directory')).toBeDefined();
    expect(screen.getByText('Project Management')).toBeDefined();
    expect(screen.getByText('Demand Forecast')).toBeDefined();
    expect(screen.getByText('Scenario Planning')).toBeDefined();
    expect(screen.getByText('Recommendations')).toBeDefined();
  });

  it('renders dynamic Breadcrumbs based on current URL path', () => {
    render(
      <MemoryRouter initialEntries={['/scenarios']}>
        <Breadcrumbs />
      </MemoryRouter>
    );

    expect(screen.getByText('Scenario Planning & Simulation')).toBeDefined();
  });
});

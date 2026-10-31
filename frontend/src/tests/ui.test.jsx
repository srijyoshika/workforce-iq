import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import KpiStatCard from '../components/ui/KpiStatCard';
import EmptyState from '../components/ui/EmptyState';
import Tabs from '../components/ui/Tabs';

describe('WorkforceIQ UI Components', () => {
  it('renders Badge with custom variants', () => {
    const { rerender } = render(<Badge variant="critical">Critical Anomaly</Badge>);
    expect(screen.getByText('Critical Anomaly')).toBeDefined();

    rerender(<Badge variant="teal">Normal 85%</Badge>);
    expect(screen.getByText('Normal 85%')).toBeDefined();
  });

  it('renders Button with variants and loading state', () => {
    const { unmount } = render(<Button variant="primary">Submit Demand</Button>);
    expect(screen.getByRole('button', { name: /Submit Demand/i })).toBeDefined();
    unmount();

    render(<Button isLoading>Saving...</Button>);
    expect(screen.getByRole('button')).toBeDefined();
    expect(screen.getByText('Saving...')).toBeDefined();
  });

  it('renders Card with header and content', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Forecast Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Total hours: 1,200</p>
        </CardContent>
      </Card>
    );

    expect(screen.getByText('Forecast Summary')).toBeDefined();
    expect(screen.getByText('Total hours: 1,200')).toBeDefined();
  });

  it('renders KpiStatCard with value, subtitle and trend indicators', () => {
    render(
      <KpiStatCard
        title="Active Capacity"
        value="160,000 hrs"
        subtitle="+4.2% vs last quarter"
        trend="up"
        trendValue="+4.2%"
      />
    );

    expect(screen.getByText('Active Capacity')).toBeDefined();
    expect(screen.getByText('160,000 hrs')).toBeDefined();
    expect(screen.getByText('+4.2% vs last quarter')).toBeDefined();
  });

  it('renders EmptyState with action button', () => {
    render(
      <EmptyState
        title="No Allocations Found"
        description="There are currently no staff allocations matching the filter criteria."
        actionLabel="Create Allocation"
        onAction={() => {}}
      />
    );

    expect(screen.getByText('No Allocations Found')).toBeDefined();
    expect(screen.getByRole('button', { name: /Create Allocation/i })).toBeDefined();
  });

  it('renders Tabs with active state and count badges', () => {
    const tabs = [
      { id: 'skills', label: 'Competencies', count: 12 },
      { id: 'allocations', label: 'Projects', count: 3 },
    ];

    render(<Tabs tabs={tabs} activeTab="skills" onTabChange={() => {}} />);
    expect(screen.getByText('Competencies')).toBeDefined();
    expect(screen.getByText('Projects')).toBeDefined();
  });
});

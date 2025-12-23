import { Briefcase, Calendar, FileCheck, Clock, RefreshCw, Brain, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { StatCard } from '@/components/dashboard/StatCard';
import { CaseTable } from '@/components/dashboard/CaseTable';
import { AddCaseModal } from '@/components/dashboard/AddCaseModal';
import { ComingSoonCard } from '@/components/dashboard/ComingSoonCard';
import { mockCases } from '@/data/mockCases';
import { useToast } from '@/hooks/use-toast';

export default function Dashboard() {
  const { toast } = useToast();
  const activeCases = mockCases.filter(c => c.status === 'pending' || c.status === 'reserved');
  const thisWeekHearings = mockCases.filter(c => c.nextHearingDate !== null).length;
  const disposedCases = mockCases.filter(c => c.status === 'disposed').length;

  const handleRefresh = () => {
    toast({
      title: "Refreshing Cases",
      description: "Syncing latest updates from eCourts...",
    });
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Track and manage your legal cases</p>
        </div>
        <div className="flex items-center gap-3">
          <Button 
            variant="outline" 
            onClick={handleRefresh}
            className="border-border hover:bg-muted"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh All
          </Button>
          <AddCaseModal />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        <div className="animate-slide-up" style={{ animationDelay: '0ms' }}>
          <StatCard
            title="Total Cases"
            value={mockCases.length}
            subtitle="All tracked cases"
            icon={Briefcase}
            variant="default"
          />
        </div>
        <div className="animate-slide-up" style={{ animationDelay: '100ms' }}>
          <StatCard
            title="Active Cases"
            value={activeCases.length}
            subtitle="Pending & Reserved"
            icon={Clock}
            variant="warning"
          />
        </div>
        <div className="animate-slide-up" style={{ animationDelay: '200ms' }}>
          <StatCard
            title="Hearings This Week"
            value={thisWeekHearings}
            subtitle="Upcoming hearings"
            icon={Calendar}
            variant="accent"
          />
        </div>
        <div className="animate-slide-up" style={{ animationDelay: '300ms' }}>
          <StatCard
            title="Disposed"
            value={disposedCases}
            subtitle="Completed cases"
            icon={FileCheck}
            variant="success"
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cases Table */}
        <div className="lg:col-span-2 animate-slide-up" style={{ animationDelay: '400ms' }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-xl font-semibold text-foreground">Active Cases</h2>
            <Button variant="link" className="text-accent hover:text-accent/80 p-0">
              View All →
            </Button>
          </div>
          <CaseTable cases={activeCases} />
        </div>

        {/* Coming Soon Section */}
        <div className="space-y-4 animate-slide-up" style={{ animationDelay: '500ms' }}>
          <h2 className="font-display text-xl font-semibold text-foreground">Future Features</h2>
          <ComingSoonCard
            title="AI Judgement Predictor"
            description="Get AI-powered predictions on case outcomes based on historical data and precedents."
            icon={Brain}
          />
          <ComingSoonCard
            title="Client Portal"
            description="Allow clients to view case status, documents, and hearing dates through a secure portal."
            icon={Users}
          />
        </div>
      </div>
    </div>
  );
}

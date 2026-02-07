import { useState, useEffect } from 'react';
import { Briefcase, Calendar, FileCheck, Clock, RefreshCw, Brain, Users, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { StatCard } from '@/components/dashboard/StatCard';
import { CaseTable } from '@/components/dashboard/CaseTable';
import { AddCaseModal } from '@/components/dashboard/AddCaseModal';
import { ComingSoonCard } from '@/components/dashboard/ComingSoonCard';
import { LegalCase } from '@/types/case';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

export default function Dashboard() {
  const { toast } = useToast();
  const [cases, setCases] = useState<LegalCase[]>([]);
  const [stats, setStats] = useState({
    total_cases: 0,
    pending_cases: 0,
    disposed_cases: 0,
    storage_stats: { cases: 0, case_types: 0, act_types: 0, courts: 0 }
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load cases and stats in parallel
      const [casesResponse, statsResponse] = await Promise.all([
        apiClient.getCases(0, 50), // Get first 50 cases for dashboard
        apiClient.getCaseStats()
      ]);

      if (casesResponse.error) {
        throw new Error(casesResponse.error);
      }

      if (casesResponse.data) {
        const convertedCases = casesResponse.data.map(caseData => apiClient.convertToLegalCase(caseData));
        setCases(convertedCases);
      }

      if (statsResponse.data) {
        setStats(statsResponse.data);
      }

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast({
        title: "Error Loading Dashboard",
        description: error instanceof Error ? error.message : "Failed to load dashboard data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      toast({
        title: "Refreshing Cases",
        description: "Syncing latest updates from eCourts...",
      });

      // Trigger bulk refresh
      const response = await apiClient.bulkRefreshCases({});
      
      if (response.error) {
        throw new Error(response.error);
      }

      // Reload dashboard data
      await loadDashboardData();

      toast({
        title: "Refresh Complete",
        description: response.data?.stats ? 
          `Updated: ${response.data.stats.updated}, Failed: ${response.data.stats.failed}` :
          "Cases have been refreshed successfully",
      });

    } catch (error) {
      console.error('Error refreshing cases:', error);
      toast({
        title: "Refresh Failed",
        description: error instanceof Error ? error.message : "Failed to refresh cases",
        variant: "destructive",
      });
    } finally {
      setRefreshing(false);
    }
  };

  const handleCaseAdded = (newCase: LegalCase) => {
    setCases(prev => [newCase, ...prev]);
    setStats(prev => ({
      ...prev,
      total_cases: prev.total_cases + 1,
      pending_cases: newCase.status === 'pending' ? prev.pending_cases + 1 : prev.pending_cases
    }));
  };

  const activeCases = cases.filter(c => c.status === 'pending' || c.status === 'reserved');
  const thisWeekHearings = cases.filter(c => c.nextHearingDate !== null).length;

  if (loading) {
    return (
      <div className="p-6 lg:p-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex items-center gap-2">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span>Loading dashboard...</span>
          </div>
        </div>
      </div>
    );
  }

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
            disabled={refreshing}
            className="border-border hover:bg-muted"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh All
          </Button>
          <AddCaseModal onAddCase={handleCaseAdded} />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        <div className="animate-slide-up" style={{ animationDelay: '0ms' }}>
          <StatCard
            title="Total Cases"
            value={stats.total_cases}
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
            value={stats.disposed_cases}
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
          <CaseTable cases={activeCases} onRefresh={loadDashboardData} />
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

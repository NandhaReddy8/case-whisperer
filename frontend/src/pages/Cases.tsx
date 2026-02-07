import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CaseTable } from '@/components/dashboard/CaseTable';
import { AddCaseModal } from '@/components/dashboard/AddCaseModal';
import { Search, Filter, Loader2, RefreshCw } from 'lucide-react';
import { LegalCase } from '@/types/case';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

export default function Cases() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [cases, setCases] = useState<LegalCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getCases(0, 100, statusFilter === 'all' ? undefined : statusFilter);
      
      if (response.error) {
        throw new Error(response.error);
      }

      if (response.data) {
        const convertedCases = response.data.map(caseData => apiClient.convertToLegalCase(caseData));
        setCases(convertedCases);
      }
    } catch (error) {
      console.error('Error loading cases:', error);
      toast({
        title: "Error Loading Cases",
        description: error instanceof Error ? error.message : "Failed to load cases",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      await loadCases();
      toast({
        title: "Cases Refreshed",
        description: "Case data has been updated successfully",
      });
    } catch (error) {
      // Error already handled in loadCases
    } finally {
      setRefreshing(false);
    }
  };

  const handleCaseAdded = (newCase: LegalCase) => {
    setCases(prev => [newCase, ...prev]);
  };

  const filteredCases = cases.filter(c => {
    const matchesSearch = 
      c.caseNo.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.petitioner.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.respondent.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.cnrNumber.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <div className="p-6 lg:p-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex items-center gap-2">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span>Loading cases...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-foreground">All Cases</h1>
          <p className="text-muted-foreground mt-1">{cases.length} cases in total</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <AddCaseModal onAddCase={handleCaseAdded} />
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 animate-slide-up">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by case number, party name, or CNR..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <Filter className="w-4 h-4 mr-2" />
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="disposed">Disposed</SelectItem>
            <SelectItem value="reserved">Reserved</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="animate-slide-up" style={{ animationDelay: '100ms' }}>
        <CaseTable cases={filteredCases} onRefresh={loadCases} />
      </div>
    </div>
  );
}

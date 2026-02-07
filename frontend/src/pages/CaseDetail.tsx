import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { 
  ArrowLeft, 
  Calendar, 
  User, 
  Building2, 
  FileText,
  RefreshCw,
  ExternalLink,
  CheckCircle2,
  Circle,
  Clock,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { format, parseISO } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import { LegalCase } from '@/types/case';
import { apiClient } from '@/lib/api';

export default function CaseDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [caseData, setCaseData] = useState<LegalCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [syncCalendar, setSyncCalendar] = useState(false);

  useEffect(() => {
    if (id) {
      loadCaseData();
    }
  }, [id]);

  const loadCaseData = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      const response = await apiClient.getCase(parseInt(id));
      
      if (response.error) {
        throw new Error(response.error);
      }

      if (response.data) {
        const convertedCase = apiClient.convertToLegalCase(response.data);
        setCaseData(convertedCase);
        setSyncCalendar(convertedCase.syncCalendar);
      }
    } catch (error) {
      console.error('Error loading case:', error);
      toast({
        title: "Error Loading Case",
        description: error instanceof Error ? error.message : "Failed to load case details",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!id || !caseData) return;
    
    try {
      setRefreshing(true);
      toast({
        title: "Refreshing Case",
        description: "Fetching latest updates from eCourts...",
      });

      const response = await apiClient.refreshCase(parseInt(id), false);
      
      if (response.error) {
        throw new Error(response.error);
      }

      if (response.data) {
        const convertedCase = apiClient.convertToLegalCase(response.data);
        setCaseData(convertedCase);
        toast({
          title: "Case Refreshed",
          description: "Case data has been updated successfully",
        });
      }
    } catch (error) {
      console.error('Error refreshing case:', error);
      toast({
        title: "Refresh Failed",
        description: error instanceof Error ? error.message : "Failed to refresh case",
        variant: "destructive",
      });
    } finally {
      setRefreshing(false);
    }
  };

  const handleCalendarToggle = async (checked: boolean) => {
    if (!id) return;
    
    try {
      const response = await apiClient.updateCase(parseInt(id), {
        sync_calendar: checked
      });
      
      if (response.error) {
        throw new Error(response.error);
      }

      setSyncCalendar(checked);
      toast({
        title: checked ? "Calendar Sync Enabled" : "Calendar Sync Disabled",
        description: checked 
          ? "Hearing dates will be synced to Google Calendar"
          : "Calendar sync has been turned off",
      });
    } catch (error) {
      console.error('Error updating calendar sync:', error);
      toast({
        title: "Update Failed",
        description: "Failed to update calendar sync setting",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="p-6 lg:p-8 max-w-6xl mx-auto">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex items-center gap-2">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span>Loading case details...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="p-8 text-center">
        <h2 className="font-display text-2xl font-bold text-foreground mb-4">Case Not Found</h2>
        <Button onClick={() => navigate('/')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      {/* Back Button */}
      <Button 
        variant="ghost" 
        onClick={() => navigate('/')}
        className="text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Dashboard
      </Button>

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 animate-slide-up">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="font-display text-2xl lg:text-3xl font-bold text-foreground">
              {caseData.caseNo}
            </h1>
            <Badge 
              variant="outline"
              className={cn(
                "font-medium capitalize",
                caseData.status === 'pending' && "border-warning/50 bg-warning/10 text-warning",
                caseData.status === 'disposed' && "border-success/50 bg-success/10 text-success",
                caseData.status === 'reserved' && "border-accent/50 bg-accent/10 text-accent"
              )}
            >
              {caseData.status}
            </Badge>
          </div>
          <p className="text-muted-foreground">{caseData.caseType}</p>
        </div>
        <div className="flex items-center gap-3">
          <Button 
            variant="outline" 
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button className="bg-accent hover:bg-accent/90 text-accent-foreground">
            <ExternalLink className="w-4 h-4 mr-2" />
            View on eCourts
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Case Details */}
        <div className="lg:col-span-1 space-y-6">
          {/* Case Info Card */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-4 animate-slide-up" style={{ animationDelay: '100ms' }}>
            <h3 className="font-display font-semibold text-foreground flex items-center gap-2">
              <FileText className="w-4 h-4 text-accent" />
              Case Information
            </h3>
            
            <div className="space-y-3">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">CNR Number</p>
                <p className="font-mono text-sm text-foreground">{caseData.cnrNumber}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Filing Date</p>
                <p className="text-sm text-foreground">
                  {caseData.filingDate ? format(parseISO(caseData.filingDate), 'dd MMMM yyyy') : 'Not available'}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Next Hearing</p>
                <p className={cn(
                  "text-sm font-medium",
                  caseData.nextHearingDate ? "text-accent" : "text-muted-foreground"
                )}>
                  {caseData.nextHearingDate 
                    ? format(parseISO(caseData.nextHearingDate), 'dd MMMM yyyy')
                    : 'No hearing scheduled'
                  }
                </p>
              </div>
            </div>
          </div>

          {/* Court Info */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-4 animate-slide-up" style={{ animationDelay: '200ms' }}>
            <h3 className="font-display font-semibold text-foreground flex items-center gap-2">
              <Building2 className="w-4 h-4 text-accent" />
              Court Details
            </h3>
            <p className="text-sm text-foreground">{caseData.courtName}</p>
          </div>

          {/* Parties */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-4 animate-slide-up" style={{ animationDelay: '300ms' }}>
            <h3 className="font-display font-semibold text-foreground flex items-center gap-2">
              <User className="w-4 h-4 text-accent" />
              Parties & Advocates
            </h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Petitioner</p>
                <p className="text-sm font-medium text-foreground">{caseData.petitioner}</p>
                <p className="text-xs text-muted-foreground mt-1">{caseData.advocates.petitioner}</p>
              </div>
              <Separator />
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Respondent</p>
                <p className="text-sm font-medium text-foreground">{caseData.respondent}</p>
                <p className="text-xs text-muted-foreground mt-1">{caseData.advocates.respondent}</p>
              </div>
            </div>
          </div>

          {/* Calendar Sync */}
          <div className="rounded-xl border border-border bg-card p-6 animate-slide-up" style={{ animationDelay: '400ms' }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-accent" />
                <div>
                  <Label htmlFor="calendar-sync" className="font-medium text-foreground">
                    Sync with Google Calendar
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Auto-sync hearing dates
                  </p>
                </div>
              </div>
              <Switch
                id="calendar-sync"
                checked={syncCalendar}
                onCheckedChange={handleCalendarToggle}
              />
            </div>
          </div>
        </div>

        {/* Right Column - Case History Timeline */}
        <div className="lg:col-span-2 animate-slide-up" style={{ animationDelay: '200ms' }}>
          <div className="rounded-xl border border-border bg-card p-6">
            <h3 className="font-display font-semibold text-foreground flex items-center gap-2 mb-6">
              <Clock className="w-4 h-4 text-accent" />
              Case History
            </h3>

            <div className="relative space-y-0">
              {caseData.history && caseData.history.length > 0 ? (
                caseData.history.map((item, index) => {
                  const isLast = index === caseData.history.length - 1;
                  const hasOrder = item.order !== null;

                  return (
                    <div key={item.id} className="relative flex gap-4 pb-8">
                      {/* Timeline Line */}
                      {!isLast && (
                        <div className="absolute left-[11px] top-8 w-0.5 h-full bg-border" />
                      )}
                      
                      {/* Timeline Dot */}
                      <div className="relative z-10 flex-shrink-0">
                        {hasOrder ? (
                          <div className="w-6 h-6 rounded-full bg-accent/10 flex items-center justify-center">
                            <CheckCircle2 className="w-4 h-4 text-accent" />
                          </div>
                        ) : (
                          <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center">
                            <Circle className="w-3 h-3 text-muted-foreground" />
                          </div>
                        )}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p className="text-sm font-medium text-foreground">{item.purpose}</p>
                            {item.order && (
                              <p className="text-sm text-accent mt-1">Order: {item.order}</p>
                            )}
                            {item.nextPurpose && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Next: {item.nextPurpose}
                              </p>
                            )}
                            {item.judge && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Judge: {item.judge}
                              </p>
                            )}
                          </div>
                          <time className="text-xs text-muted-foreground whitespace-nowrap">
                            {format(parseISO(item.date), 'dd MMM yyyy')}
                          </time>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No case history available</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

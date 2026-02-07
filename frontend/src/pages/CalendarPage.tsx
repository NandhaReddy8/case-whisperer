import { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { format, parseISO, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths } from 'date-fns';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';
import { LegalCase } from '@/types/case';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [cases, setCases] = useState<LegalCase[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getCases(0, 100);
      
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

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd });

  // Get cases with hearings
  const casesWithHearings = cases.filter(c => c.nextHearingDate !== null);

  // Get hearings for a specific day
  const getHearingsForDay = (day: Date) => {
    return casesWithHearings.filter(c => 
      c.nextHearingDate && isSameDay(parseISO(c.nextHearingDate), day)
    );
  };

  // Get weekday headers
  const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  // Calculate start offset for the first day of month
  const startOffset = monthStart.getDay();

  if (loading) {
    return (
      <div className="p-6 lg:p-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex items-center gap-2">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span>Loading calendar...</span>
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
          <h1 className="font-display text-3xl font-bold text-foreground">Calendar</h1>
          <p className="text-muted-foreground mt-1">View upcoming hearings and court dates</p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="icon"
            onClick={() => setCurrentDate(subMonths(currentDate, 1))}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="font-display text-lg font-semibold min-w-[160px] text-center">
            {format(currentDate, 'MMMM yyyy')}
          </span>
          <Button 
            variant="outline" 
            size="icon"
            onClick={() => setCurrentDate(addMonths(currentDate, 1))}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="rounded-xl border border-border bg-card overflow-hidden animate-slide-up">
        {/* Weekday Headers */}
        <div className="grid grid-cols-7 bg-muted/50">
          {weekdays.map(day => (
            <div key={day} className="p-3 text-center text-sm font-medium text-muted-foreground border-b border-border">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar Days */}
        <div className="grid grid-cols-7">
          {/* Empty cells for start offset */}
          {Array.from({ length: startOffset }).map((_, i) => (
            <div key={`empty-${i}`} className="min-h-[100px] p-2 border-b border-r border-border bg-muted/20" />
          ))}

          {/* Actual days */}
          {days.map((day, index) => {
            const hearings = getHearingsForDay(day);
            const isToday = isSameDay(day, new Date());

            return (
              <div 
                key={day.toISOString()}
                className={cn(
                  "min-h-[100px] p-2 border-b border-r border-border transition-colors",
                  isToday && "bg-accent/5",
                  hearings.length > 0 && "cursor-pointer hover:bg-muted/50"
                )}
              >
                <div className={cn(
                  "w-7 h-7 flex items-center justify-center rounded-full text-sm mb-2",
                  isToday && "bg-accent text-accent-foreground font-semibold"
                )}>
                  {format(day, 'd')}
                </div>
                
                <div className="space-y-1">
                  {hearings.slice(0, 2).map(hearing => (
                    <div
                      key={hearing.id}
                      onClick={() => navigate(`/cases/${hearing.id}`)}
                      className="p-1.5 rounded bg-accent/10 border border-accent/20 cursor-pointer hover:bg-accent/20 transition-colors"
                    >
                      <p className="text-xs font-medium text-accent truncate">
                        {hearing.caseNo}
                      </p>
                    </div>
                  ))}
                  {hearings.length > 2 && (
                    <Badge variant="outline" className="text-xs">
                      +{hearings.length - 2} more
                    </Badge>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Upcoming Hearings List */}
      <div className="animate-slide-up" style={{ animationDelay: '100ms' }}>
        <h2 className="font-display text-xl font-semibold text-foreground mb-4">Upcoming Hearings</h2>
        <div className="space-y-3">
          {casesWithHearings.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <CalendarIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No upcoming hearings scheduled</p>
            </div>
          ) : (
            casesWithHearings.map(caseItem => (
              <div
                key={caseItem.id}
                onClick={() => navigate(`/cases/${caseItem.id}`)}
                className="flex items-center justify-between p-4 rounded-lg border border-border bg-card hover:bg-muted/50 cursor-pointer transition-colors"
              >
                <div className="space-y-1">
                  <p className="font-medium text-foreground">{caseItem.caseNo}</p>
                  <p className="text-sm text-muted-foreground">
                    {caseItem.petitioner} vs. {caseItem.respondent}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-accent">
                    {caseItem.nextHearingDate && format(parseISO(caseItem.nextHearingDate), 'dd MMM yyyy')}
                  </p>
                  <p className="text-xs text-muted-foreground">{caseItem.courtName}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

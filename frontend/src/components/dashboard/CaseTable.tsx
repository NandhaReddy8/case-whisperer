import { useNavigate } from 'react-router-dom';
import { LegalCase } from '@/types/case';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Calendar, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format, parseISO, isValid } from 'date-fns';

interface CaseTableProps {
  cases: LegalCase[];
}

function formatDate(dateString: string | null): string {
  if (!dateString) return '—';
  const date = parseISO(dateString);
  if (!isValid(date)) return '—';
  return format(date, 'dd MMM yyyy');
}

function StatusBadge({ status }: { status: LegalCase['status'] }) {
  return (
    <Badge 
      variant="outline"
      className={cn(
        "font-medium capitalize",
        status === 'pending' && "border-warning/50 bg-warning/10 text-warning",
        status === 'disposed' && "border-success/50 bg-success/10 text-success",
        status === 'reserved' && "border-accent/50 bg-accent/10 text-accent"
      )}
    >
      {status}
    </Badge>
  );
}

export function CaseTable({ cases }: CaseTableProps) {
  const navigate = useNavigate();

  if (cases.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <Calendar className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="font-display text-lg font-semibold text-foreground mb-2">No cases found</h3>
        <p className="text-sm text-muted-foreground">Add your first case to get started</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50 hover:bg-muted/50">
            <TableHead className="font-semibold text-foreground">Case No.</TableHead>
            <TableHead className="font-semibold text-foreground">Parties</TableHead>
            <TableHead className="font-semibold text-foreground">Court</TableHead>
            <TableHead className="font-semibold text-foreground">Next Hearing</TableHead>
            <TableHead className="font-semibold text-foreground">Status</TableHead>
            <TableHead className="font-semibold text-foreground w-[100px]">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {cases.map((caseItem, index) => (
            <TableRow 
              key={caseItem.id}
              className={cn(
                "cursor-pointer transition-colors hover:bg-muted/50",
                "animate-fade-in"
              )}
              style={{ animationDelay: `${index * 50}ms` }}
              onClick={() => navigate(`/cases/${caseItem.id}`)}
            >
              <TableCell>
                <div className="space-y-1">
                  <p className="font-medium text-foreground">{caseItem.caseNo}</p>
                  <p className="text-xs text-muted-foreground">{caseItem.caseType}</p>
                </div>
              </TableCell>
              <TableCell>
                <div className="space-y-1 max-w-[250px]">
                  <p className="font-medium text-foreground truncate">{caseItem.petitioner}</p>
                  <p className="text-xs text-muted-foreground truncate">vs. {caseItem.respondent}</p>
                </div>
              </TableCell>
              <TableCell>
                <p className="text-sm text-foreground">{caseItem.courtName}</p>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  {caseItem.nextHearingDate && (
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                  )}
                  <span className={cn(
                    "text-sm",
                    caseItem.nextHearingDate ? "text-foreground" : "text-muted-foreground"
                  )}>
                    {formatDate(caseItem.nextHearingDate)}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <StatusBadge status={caseItem.status} />
              </TableCell>
              <TableCell>
                <Button 
                  variant="ghost" 
                  size="sm"
                  className="text-accent hover:text-accent hover:bg-accent/10"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/cases/${caseItem.id}`);
                  }}
                >
                  <ExternalLink className="w-4 h-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

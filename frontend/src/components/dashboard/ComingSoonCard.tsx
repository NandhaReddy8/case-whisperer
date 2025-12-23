import { LucideIcon, Lock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ComingSoonCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
}

export function ComingSoonCard({ title, description, icon: Icon }: ComingSoonCardProps) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-border bg-card p-6 group">
      {/* Blur overlay */}
      <div className="absolute inset-0 backdrop-blur-[2px] bg-card/50 z-10 flex flex-col items-center justify-center">
        <div className="p-3 rounded-full bg-primary/10 mb-3">
          <Lock className="w-6 h-6 text-primary" />
        </div>
        <span className="text-sm font-medium text-foreground">Coming Soon</span>
      </div>

      {/* Blurred content */}
      <div className="space-y-4 opacity-40">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent/10">
            <Icon className="w-5 h-5 text-accent" />
          </div>
          <h3 className="font-display font-semibold text-foreground">{title}</h3>
        </div>
        <p className="text-sm text-muted-foreground">{description}</p>
        <div className="space-y-2">
          <div className="h-2 w-full bg-muted rounded" />
          <div className="h-2 w-3/4 bg-muted rounded" />
          <div className="h-2 w-1/2 bg-muted rounded" />
        </div>
      </div>
    </div>
  );
}

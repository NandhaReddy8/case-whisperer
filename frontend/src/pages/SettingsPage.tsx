import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Settings, Calendar, Bell, Database, Shield, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useState } from 'react';

export default function SettingsPage() {
  const { toast } = useToast();
  const [isSaving, setIsSaving] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState('daily');

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsSaving(false);
    toast({
      title: "Settings Saved",
      description: "Your preferences have been updated successfully.",
    });
  };

  return (
    <div className="p-6 lg:p-8 max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground mt-1">Manage your application preferences</p>
      </div>

      {/* Google Calendar Integration */}
      <div className="rounded-xl border border-border bg-card p-6 space-y-4 animate-slide-up">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent/10">
            <Calendar className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="font-display font-semibold text-foreground">Google Calendar Integration</h3>
            <p className="text-sm text-muted-foreground">Sync hearing dates with your Google Calendar</p>
          </div>
        </div>
        <Separator />
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Calendar Account</Label>
              <p className="text-sm text-muted-foreground">Connect your Google account</p>
            </div>
            <Button variant="outline">
              Connect Google
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>Reminder: 1 Week Before</Label>
              <p className="text-sm text-muted-foreground">Get reminded 1 week before hearing</p>
            </div>
            <Switch defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>Reminder: 1 Day Before</Label>
              <p className="text-sm text-muted-foreground">Get reminded 1 day before hearing</p>
            </div>
            <Switch defaultChecked />
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="rounded-xl border border-border bg-card p-6 space-y-4 animate-slide-up" style={{ animationDelay: '100ms' }}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent/10">
            <Bell className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="font-display font-semibold text-foreground">Notifications</h3>
            <p className="text-sm text-muted-foreground">Configure how you receive updates</p>
          </div>
        </div>
        <Separator />
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Email Notifications</Label>
              <p className="text-sm text-muted-foreground">Receive case updates via email</p>
            </div>
            <Switch 
              checked={emailNotifications} 
              onCheckedChange={setEmailNotifications} 
            />
          </div>
          <div className="space-y-2">
            <Label>Notification Email</Label>
            <Input 
              type="email" 
              placeholder="your@email.com"
              disabled={!emailNotifications}
            />
          </div>
        </div>
      </div>

      {/* Auto Refresh */}
      <div className="rounded-xl border border-border bg-card p-6 space-y-4 animate-slide-up" style={{ animationDelay: '200ms' }}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent/10">
            <Database className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="font-display font-semibold text-foreground">Data Sync</h3>
            <p className="text-sm text-muted-foreground">Configure automatic case updates</p>
          </div>
        </div>
        <Separator />
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Auto-Refresh Cases</Label>
              <p className="text-sm text-muted-foreground">Automatically fetch latest case status</p>
            </div>
            <Switch 
              checked={autoRefresh} 
              onCheckedChange={setAutoRefresh} 
            />
          </div>
          <div className="space-y-2">
            <Label>Refresh Interval</Label>
            <Select 
              value={refreshInterval} 
              onValueChange={setRefreshInterval}
              disabled={!autoRefresh}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hourly">Every Hour</SelectItem>
                <SelectItem value="daily">Daily (3 AM)</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button 
          onClick={handleSave}
          disabled={isSaving}
          className="bg-accent hover:bg-accent/90 text-accent-foreground"
        >
          {isSaving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            'Save Changes'
          )}
        </Button>
      </div>
    </div>
  );
}

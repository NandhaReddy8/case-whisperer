import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import { Plus, Search, Hash, User, FileText, Loader2, Calendar } from 'lucide-react';
import { SearchType } from '@/types/case';
import { useToast } from '@/hooks/use-toast';
import { apiClient, CaseType, Court } from '@/lib/api';

interface AddCaseModalProps {
  onAddCase?: (data: any) => void;
}

export function AddCaseModal({ onAddCase }: AddCaseModalProps) {
  const [open, setOpen] = useState(false);
  const [searchType, setSearchType] = useState<SearchType>('cnr');
  const [isLoading, setIsLoading] = useState(false);
  const [syncCalendar, setSyncCalendar] = useState(false);
  const { toast } = useToast();

  // Dynamic data
  const [caseTypes, setCaseTypes] = useState<CaseType[]>([]);
  const [courts, setCourts] = useState<Court[]>([]);
  const [loadingCaseTypes, setLoadingCaseTypes] = useState(false);

  // Form states
  const [cnrNumber, setCnrNumber] = useState('');
  const [caseType, setCaseType] = useState('');
  const [caseNumber, setCaseNumber] = useState('');
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [diaryNumber, setDiaryNumber] = useState('');
  const [partyName, setPartyName] = useState('');
  const [selectedCourt, setSelectedCourt] = useState('6'); // Default to Gujarat

  useEffect(() => {
    if (open) {
      loadCourts();
      loadCaseTypes();
    }
  }, [open]);

  const loadCourts = async () => {
    try {
      const response = await apiClient.getCourts();
      if (response.data?.courts) {
        setCourts(response.data.courts);
      }
    } catch (error) {
      console.error('Error loading courts:', error);
    }
  };

  const loadCaseTypes = async () => {
    try {
      setLoadingCaseTypes(true);
      const response = await apiClient.getCaseTypes(selectedCourt);
      if (response.data?.case_types) {
        setCaseTypes(response.data.case_types);
      }
    } catch (error) {
      console.error('Error loading case types:', error);
    } finally {
      setLoadingCaseTypes(false);
    }
  };

  const handleSearch = async () => {
    setIsLoading(true);
    
    try {
      // Prepare search request
      const searchRequest = apiClient.convertSearchFormData({
        searchType,
        cnrNumber: cnrNumber || undefined,
        caseType: caseType || undefined,
        caseNumber: caseNumber || undefined,
        year: year || undefined,
        diaryNumber: diaryNumber || undefined,
        partyName: partyName || undefined,
        courtStateCode: selectedCourt,
      });

      // Add case using the API
      const response = await apiClient.addCase({
        search_request: searchRequest,
        sync_calendar: syncCalendar,
      });

      if (response.error) {
        throw new Error(response.error);
      }

      if (response.data) {
        const legalCase = apiClient.convertToLegalCase(response.data);
        
        toast({
          title: "Case Added Successfully",
          description: `Case ${legalCase.caseNo} has been added to your tracker.`,
        });

        // Call the callback if provided
        if (onAddCase) {
          onAddCase(legalCase);
        }

        setOpen(false);
        resetForm();
      }
    } catch (error) {
      console.error('Error adding case:', error);
      toast({
        title: "Error Adding Case",
        description: error instanceof Error ? error.message : "Failed to add case. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setCnrNumber('');
    setCaseType('');
    setCaseNumber('');
    setYear(new Date().getFullYear().toString());
    setDiaryNumber('');
    setPartyName('');
    setSyncCalendar(false);
  };

  const isFormValid = () => {
    switch (searchType) {
      case 'cnr':
        return cnrNumber.length >= 16;
      case 'case':
        return caseType && caseNumber && year;
      case 'diary':
        return diaryNumber && year;
      case 'party':
        return partyName.trim().length > 0;
      default:
        return false;
    }
  };

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 30 }, (_, i) => (currentYear - i).toString());

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-accent hover:bg-accent/90 text-accent-foreground shadow-gold">
          <Plus className="w-4 h-4 mr-2" />
          Add New Case
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px] bg-card">
        <DialogHeader>
          <DialogTitle className="font-display text-xl">Add New Case</DialogTitle>
        </DialogHeader>

        {/* Court Selection */}
        <div className="space-y-2">
          <Label>Court</Label>
          <Select value={selectedCourt} onValueChange={(value) => {
            setSelectedCourt(value);
            setCaseTypes([]); // Clear case types when court changes
            loadCaseTypes(); // Load new case types
          }}>
            <SelectTrigger>
              <SelectValue placeholder="Select court" />
            </SelectTrigger>
            <SelectContent>
              {courts.map((court) => (
                <SelectItem key={`${court.state_code}-${court.court_code}`} value={court.state_code}>
                  {court.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <Tabs value={searchType} onValueChange={(v) => setSearchType(v as SearchType)} className="mt-4">
          <TabsList className="grid grid-cols-4 w-full bg-muted">
            <TabsTrigger value="cnr" className="text-xs sm:text-sm data-[state=active]:bg-accent data-[state=active]:text-accent-foreground">
              <Hash className="w-3 h-3 mr-1 hidden sm:inline" />
              CNR
            </TabsTrigger>
            <TabsTrigger value="case" className="text-xs sm:text-sm data-[state=active]:bg-accent data-[state=active]:text-accent-foreground">
              <FileText className="w-3 h-3 mr-1 hidden sm:inline" />
              Case No
            </TabsTrigger>
            <TabsTrigger value="diary" className="text-xs sm:text-sm data-[state=active]:bg-accent data-[state=active]:text-accent-foreground">
              <FileText className="w-3 h-3 mr-1 hidden sm:inline" />
              Diary No
            </TabsTrigger>
            <TabsTrigger value="party" className="text-xs sm:text-sm data-[state=active]:bg-accent data-[state=active]:text-accent-foreground">
              <User className="w-3 h-3 mr-1 hidden sm:inline" />
              Party
            </TabsTrigger>
          </TabsList>

          <TabsContent value="cnr" className="mt-6 space-y-4 animate-fade-in">
            <div className="space-y-2">
              <Label htmlFor="cnr">CNR Number</Label>
              <Input
                id="cnr"
                placeholder="Enter 16-digit CNR Number"
                value={cnrNumber}
                onChange={(e) => setCnrNumber(e.target.value.toUpperCase())}
                maxLength={16}
                className="font-mono tracking-wider"
              />
              <p className="text-xs text-muted-foreground">
                Example: DLHC010001232024
              </p>
            </div>
          </TabsContent>

          <TabsContent value="case" className="mt-6 space-y-4 animate-fade-in">
            <div className="space-y-2">
              <Label>Case Type</Label>
              <Select value={caseType} onValueChange={setCaseType} disabled={loadingCaseTypes}>
                <SelectTrigger>
                  <SelectValue placeholder={loadingCaseTypes ? "Loading case types..." : "Select case type"} />
                </SelectTrigger>
                <SelectContent>
                  {caseTypes.map((type) => (
                    <SelectItem key={type.code} value={type.code}>
                      {type.code} - {type.description}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="caseNumber">Case Number</Label>
                <Input
                  id="caseNumber"
                  placeholder="1234"
                  value={caseNumber}
                  onChange={(e) => setCaseNumber(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="yearCase">Year</Label>
                <Select value={year} onValueChange={setYear}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {years.map((y) => (
                      <SelectItem key={y} value={y}>{y}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="diary" className="mt-6 space-y-4 animate-fade-in">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="diaryNumber">Diary Number</Label>
                <Input
                  id="diaryNumber"
                  placeholder="Enter diary number"
                  value={diaryNumber}
                  onChange={(e) => setDiaryNumber(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="yearDiary">Year</Label>
                <Select value={year} onValueChange={setYear}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {years.map((y) => (
                      <SelectItem key={y} value={y}>{y}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="party" className="mt-6 space-y-4 animate-fade-in">
            <div className="space-y-2">
              <Label htmlFor="partyName">Party Name (Petitioner/Respondent)</Label>
              <Input
                id="partyName"
                placeholder="Enter party name"
                value={partyName}
                onChange={(e) => setPartyName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="yearParty">Year</Label>
              <Select value={year} onValueChange={setYear}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {years.map((y) => (
                    <SelectItem key={y} value={y}>{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </TabsContent>
        </Tabs>

        {/* Calendar Sync Option */}
        <div className="flex items-center space-x-2 mt-4 p-3 rounded-lg bg-muted/30 border border-border">
          <Checkbox 
            id="syncCalendar" 
            checked={syncCalendar}
            onCheckedChange={(checked) => setSyncCalendar(checked as boolean)}
          />
          <Label htmlFor="syncCalendar" className="text-sm flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Sync hearing dates with Google Calendar
          </Label>
        </div>

        {/* Captcha Info */}
        <div className="mt-4 p-4 rounded-lg bg-muted/50 border border-border">
          <div className="flex items-center gap-4">
            <div className="w-32 h-12 bg-muted rounded flex items-center justify-center border border-border">
              <span className="text-xs text-muted-foreground">AUTO-SOLVE</span>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">CAPTCHA Auto-Solving</p>
              <p className="text-xs text-muted-foreground">
                CAPTCHA will be automatically solved using AI
              </p>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleSearch}
            disabled={isLoading || !isFormValid()}
            className="bg-accent hover:bg-accent/90 text-accent-foreground"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Search & Add Case
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

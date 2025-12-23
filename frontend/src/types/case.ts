export interface LegalCase {
  id: string;
  caseNo: string;
  cnrNumber: string;
  caseType: string;
  petitioner: string;
  respondent: string;
  courtName: string;
  nextHearingDate: string | null;
  status: 'pending' | 'disposed' | 'reserved';
  filingDate: string;
  advocates: {
    petitioner: string;
    respondent: string;
  };
  history: CaseHistory[];
  syncCalendar: boolean;
  lastSyncedAt: string | null;
}

export interface CaseHistory {
  id: string;
  date: string;
  purpose: string;
  order: string | null;
  nextPurpose: string | null;
}

export type SearchType = 'cnr' | 'caseNo' | 'partyName' | 'diaryNo';

export interface SearchFormData {
  searchType: SearchType;
  cnrNumber?: string;
  caseType?: string;
  caseNumber?: string;
  year?: string;
  diaryNumber?: string;
  partyName?: string;
}

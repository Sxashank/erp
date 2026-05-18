import { zodResolver } from '@hookform/resolvers/zod';
import {
  Search,
  User,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Download,
} from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import * as z from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatDate } from '@/lib/utils';

import { logger } from "@/lib/logger";
// Form schema for CKYC search
const ckycSearchSchema = z.object({
  entity_id: z.string().uuid('Please select an entity'),
  pan: z
    .string()
    .length(10, 'PAN must be exactly 10 characters')
    .regex(/^[A-Z]{5}[0-9]{4}[A-Z]$/, 'Invalid PAN format'),
  date_of_birth: z.string().optional(),
  mobile_number: z
    .string()
    .regex(/^[6-9][0-9]{9}$/, 'Invalid mobile number')
    .optional()
    .or(z.literal('')),
});

type CKYCSearchFormValues = z.infer<typeof ckycSearchSchema>;

// Types for search results
interface CKYCSearchResult {
  ckyc_number: string;
  name: string;
  pan: string;
  date_of_birth: string;
  address: string;
  photo_available: boolean;
  signature_available: boolean;
  documents_available: string[];
  last_updated: string;
}

// Mock data for demonstration
const mockSearchResults: CKYCSearchResult[] = [
  {
    ckyc_number: 'CKYC123456789012345',
    name: 'John Doe',
    pan: 'ABCPD1234F',
    date_of_birth: '1990-05-15',
    address: '123, Main Street, New Delhi - 110001',
    photo_available: true,
    signature_available: true,
    documents_available: ['PAN', 'Aadhaar', 'Address Proof'],
    last_updated: '2024-06-15',
  },
];

// Mock recent searches
const recentSearches = [
  {
    id: '1',
    pan: 'ABCPD1234F',
    entity_name: 'John Doe',
    status: 'FOUND',
    searched_at: '2024-12-20T10:30:00',
    ckyc_number: 'CKYC123456789012345',
  },
  {
    id: '2',
    pan: 'XYZPQ5678G',
    entity_name: 'ABC Corp',
    status: 'NOT_FOUND',
    searched_at: '2024-12-19T14:15:00',
    ckyc_number: null,
  },
  {
    id: '3',
    pan: 'LMNRS9012H',
    entity_name: 'Jane Smith',
    status: 'ERROR',
    searched_at: '2024-12-18T09:00:00',
    ckyc_number: null,
  },
];

const getStatusBadge = (status: string) => {
  const statusConfig: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode; label: string }> = {
    FOUND: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Found' },
    NOT_FOUND: { variant: 'secondary', icon: <XCircle className="h-3 w-3 mr-1" />, label: 'Not Found' },
    PENDING: { variant: 'outline', icon: <Clock className="h-3 w-3 mr-1" />, label: 'Pending' },
    ERROR: { variant: 'destructive', icon: <AlertCircle className="h-3 w-3 mr-1" />, label: 'Error' },
  };

  const config = statusConfig[status] || statusConfig.PENDING;
  return (
    <Badge variant={config.variant} className="flex items-center w-fit">
      {config.icon}
      {config.label}
    </Badge>
  );
};

export default function CKYCSearch() {
  const navigate = useNavigate();
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<CKYCSearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  const form = useForm<CKYCSearchFormValues>({
    resolver: zodResolver(ckycSearchSchema),
    defaultValues: {
      entity_id: '',
      pan: '',
      date_of_birth: '',
      mobile_number: '',
    },
  });

  const onSubmit = async (data: CKYCSearchFormValues) => {
    setIsSearching(true);
    setHasSearched(false);

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Mock result - in real implementation, call the API
      setSearchResults(mockSearchResults);
      setHasSearched(true);
    } catch (error) {
      logger.error('CKYC Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleDownload = (ckycNumber: string) => {
    navigate(`/admin/kyc/ckyc/download?ckyc=${ckycNumber}`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="CKYC Search"
        subtitle="Search Central KYC Registry by PAN to retrieve customer KYC records"
        actions={
          <Button variant="outline" onClick={() => navigate('/admin/kyc/ckyc/status')}>
            <FileText className="h-4 w-4 mr-2" />
            View Transaction History
          </Button>
        }
      />

      {/* Info Alert */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>CKYC Registry</AlertTitle>
        <AlertDescription>
          CKYC (Central Know Your Customer) is a centralized repository of KYC records maintained
          by CERSAI. Search using PAN to check if a customer's KYC is already registered.
        </AlertDescription>
      </Alert>

      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Search CKYC Registry
          </CardTitle>
          <CardDescription>
            Enter PAN and optionally date of birth or mobile to search for CKYC records
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FormField
                  control={form.control}
                  name="pan"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>PAN Number *</FormLabel>
                      <FormControl>
                        <Input
                          {...field}
                          placeholder="ABCDE1234F"
                          className="uppercase"
                          maxLength={10}
                          onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                        />
                      </FormControl>
                      <FormDescription>10-character Permanent Account Number</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="date_of_birth"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Date of Birth</FormLabel>
                      <FormControl>
                        <Input {...field} type="date" />
                      </FormControl>
                      <FormDescription>Optional - helps in exact matching</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="mobile_number"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Mobile Number</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="9876543210" maxLength={10} />
                      </FormControl>
                      <FormDescription>Optional - 10-digit mobile number</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="flex justify-end">
                <Button type="submit" disabled={isSearching}>
                  {isSearching ? (
                    <>
                      <Clock className="h-4 w-4 mr-2 animate-spin" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Search className="h-4 w-4 mr-2" />
                      Search CKYC
                    </>
                  )}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>

      {/* Search Results */}
      {hasSearched && (
        <Card>
          <CardHeader>
            <CardTitle>Search Results</CardTitle>
            <CardDescription>
              {searchResults.length > 0
                ? `Found ${searchResults.length} CKYC record(s)`
                : 'No CKYC records found for the given PAN'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {searchResults.length > 0 ? (
              <div className="space-y-4">
                {searchResults.map((result) => (
                  <Card key={result.ckyc_number} className="border-green-200 bg-green-50">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="space-y-3">
                          <div className="flex items-center gap-3">
                            <User className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <div className="font-semibold text-lg">{result.name}</div>
                              <div className="text-sm text-muted-foreground">
                                CKYC: {result.ckyc_number}
                              </div>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <Label className="text-xs text-muted-foreground">PAN</Label>
                              <div className="font-medium">{result.pan}</div>
                            </div>
                            <div>
                              <Label className="text-xs text-muted-foreground">Date of Birth</Label>
                              <div className="font-medium">{formatDate(result.date_of_birth)}</div>
                            </div>
                            <div>
                              <Label className="text-xs text-muted-foreground">Last Updated</Label>
                              <div className="font-medium">{formatDate(result.last_updated)}</div>
                            </div>
                            <div>
                              <Label className="text-xs text-muted-foreground">
                                Documents Available
                              </Label>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {result.documents_available.map((doc) => (
                                  <Badge key={doc} variant="outline" className="text-xs">
                                    {doc}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </div>

                          <div>
                            <Label className="text-xs text-muted-foreground">Address</Label>
                            <div className="text-sm">{result.address}</div>
                          </div>

                          <div className="flex gap-2">
                            {result.photo_available && (
                              <Badge variant="secondary">Photo Available</Badge>
                            )}
                            {result.signature_available && (
                              <Badge variant="secondary">Signature Available</Badge>
                            )}
                          </div>
                        </div>

                        <Button onClick={() => handleDownload(result.ckyc_number)}>
                          <Download className="h-4 w-4 mr-2" />
                          Download Record
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <XCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <div className="text-lg font-medium">No CKYC Record Found</div>
                <p className="text-muted-foreground mt-2">
                  No CKYC record exists for the given PAN. You may need to create a new CKYC
                  registration for this customer.
                </p>
                <Button variant="outline" className="mt-4">
                  Create CKYC Registration
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Recent Searches */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Searches</CardTitle>
          <CardDescription>Your recent CKYC search transactions</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>PAN</TableHead>
                <TableHead>Entity Name</TableHead>
                <TableHead>Searched At</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>CKYC Number</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentSearches.map((search) => (
                <TableRow key={search.id}>
                  <TableCell className="font-medium">{search.pan}</TableCell>
                  <TableCell>{search.entity_name}</TableCell>
                  <TableCell>{formatDate(search.searched_at)}</TableCell>
                  <TableCell>{getStatusBadge(search.status)}</TableCell>
                  <TableCell>
                    {search.ckyc_number || (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {search.ckyc_number && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDownload(search.ckyc_number!)}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

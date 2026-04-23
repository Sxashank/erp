import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Download,
  FileText,
  User,
  CheckCircle,
  Clock,
  AlertCircle,
  Eye,
  Image,
  FileBadge,
  MapPin,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatDate } from '@/lib/utils';

// Form schema for CKYC download
const ckycDownloadSchema = z.object({
  ckyc_number: z
    .string()
    .min(14, 'CKYC number must be at least 14 characters')
    .max(20, 'CKYC number must not exceed 20 characters'),
  entity_id: z.string().uuid('Please select an entity').optional(),
  download_photo: z.boolean().default(true),
  download_signature: z.boolean().default(true),
  download_documents: z.boolean().default(true),
});

type CKYCDownloadFormValues = z.infer<typeof ckycDownloadSchema>;

// Types for downloaded record
interface CKYCRecord {
  ckyc_number: string;
  registration_date: string;
  last_updated: string;
  personal_details: {
    title: string;
    first_name: string;
    middle_name: string;
    last_name: string;
    maiden_name?: string;
    father_name: string;
    mother_name: string;
    spouse_name?: string;
    date_of_birth: string;
    gender: string;
    marital_status: string;
    nationality: string;
    residential_status: string;
    occupation: string;
  };
  identity_details: {
    pan: string;
    aadhaar_masked: string;
    passport?: string;
    voter_id?: string;
    driving_license?: string;
  };
  contact_details: {
    mobile: string;
    email: string;
    landline?: string;
  };
  addresses: {
    type: string;
    address_line1: string;
    address_line2?: string;
    city: string;
    district: string;
    state: string;
    pincode: string;
    country: string;
  }[];
  photo_url?: string;
  signature_url?: string;
  documents: {
    type: string;
    number: string;
    expiry_date?: string;
    verified: boolean;
  }[];
}

// Mock downloaded record
const mockCKYCRecord: CKYCRecord = {
  ckyc_number: 'CKYC123456789012345',
  registration_date: '2022-03-15',
  last_updated: '2024-06-15',
  personal_details: {
    title: 'Mr',
    first_name: 'John',
    middle_name: '',
    last_name: 'Doe',
    father_name: 'Robert Doe',
    mother_name: 'Mary Doe',
    spouse_name: 'Jane Doe',
    date_of_birth: '1990-05-15',
    gender: 'Male',
    marital_status: 'Married',
    nationality: 'Indian',
    residential_status: 'Resident',
    occupation: 'Salaried',
  },
  identity_details: {
    pan: 'ABCPD1234F',
    aadhaar_masked: 'XXXX-XXXX-5678',
    passport: 'P1234567',
    voter_id: 'ABC1234567',
    driving_license: 'DL-0120230012345',
  },
  contact_details: {
    mobile: '9876543210',
    email: 'john.doe@example.com',
    landline: '011-12345678',
  },
  addresses: [
    {
      type: 'Permanent',
      address_line1: '123, Main Street',
      address_line2: 'Near Central Park',
      city: 'New Delhi',
      district: 'Central Delhi',
      state: 'Delhi',
      pincode: '110001',
      country: 'India',
    },
    {
      type: 'Current',
      address_line1: '456, Business Tower',
      address_line2: 'Sector 5',
      city: 'Gurugram',
      district: 'Gurugram',
      state: 'Haryana',
      pincode: '122001',
      country: 'India',
    },
  ],
  photo_url: '/placeholder-photo.jpg',
  signature_url: '/placeholder-signature.jpg',
  documents: [
    { type: 'PAN Card', number: 'ABCPD1234F', verified: true },
    { type: 'Aadhaar Card', number: 'XXXX-XXXX-5678', verified: true },
    { type: 'Passport', number: 'P1234567', expiry_date: '2030-12-31', verified: true },
    { type: 'Voter ID', number: 'ABC1234567', verified: true },
  ],
};

export default function CKYCDownload() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const ckycFromUrl = searchParams.get('ckyc') || '';

  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadedRecord, setDownloadedRecord] = useState<CKYCRecord | null>(null);
  const [hasDownloaded, setHasDownloaded] = useState(false);

  const form = useForm<CKYCDownloadFormValues>({
    resolver: zodResolver(ckycDownloadSchema) as any,
    defaultValues: {
      ckyc_number: ckycFromUrl,
      entity_id: '',
      download_photo: true,
      download_signature: true,
      download_documents: true,
    },
  });

  const onSubmit = async (data: CKYCDownloadFormValues) => {
    setIsDownloading(true);
    setHasDownloaded(false);

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Mock result
      setDownloadedRecord(mockCKYCRecord);
      setHasDownloaded(true);
    } catch (error) {
      console.error('CKYC Download failed:', error);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleSaveToEntity = () => {
    // Save the downloaded CKYC record to the entity
    alert('CKYC record saved to entity successfully!');
    navigate('/admin/lending/entities');
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="CKYC Download"
        subtitle="Download complete KYC records from Central KYC Registry"
        actions={
          <Button variant="outline" onClick={() => navigate('/admin/kyc/ckyc/search')}>
            <FileText className="h-4 w-4 mr-2" />
            Search CKYC
          </Button>
        }
      />

      {/* Download Form */}
      {!hasDownloaded && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Download CKYC Record
            </CardTitle>
            <CardDescription>
              Enter the CKYC number to download the complete KYC record
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit as any)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="ckyc_number"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>CKYC Number *</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="CKYC123456789012345" className="uppercase" />
                      </FormControl>
                      <FormDescription>14-20 character CKYC identifier</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="space-y-4">
                  <Label>Download Options</Label>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <FormField
                      control={form.control}
                      name="download_photo"
                      render={({ field }) => (
                        <FormItem className="flex items-center space-x-3 space-y-0 border rounded-lg p-4">
                          <FormControl>
                            <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                          </FormControl>
                          <div className="flex items-center gap-2">
                            <Image className="h-4 w-4 text-muted-foreground" />
                            <FormLabel className="cursor-pointer">Photo</FormLabel>
                          </div>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="download_signature"
                      render={({ field }) => (
                        <FormItem className="flex items-center space-x-3 space-y-0 border rounded-lg p-4">
                          <FormControl>
                            <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                          </FormControl>
                          <div className="flex items-center gap-2">
                            <FileBadge className="h-4 w-4 text-muted-foreground" />
                            <FormLabel className="cursor-pointer">Signature</FormLabel>
                          </div>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="download_documents"
                      render={({ field }) => (
                        <FormItem className="flex items-center space-x-3 space-y-0 border rounded-lg p-4">
                          <FormControl>
                            <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                          </FormControl>
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            <FormLabel className="cursor-pointer">Documents</FormLabel>
                          </div>
                        </FormItem>
                      )}
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button type="submit" disabled={isDownloading}>
                    {isDownloading ? (
                      <>
                        <Clock className="h-4 w-4 mr-2 animate-spin" />
                        Downloading...
                      </>
                    ) : (
                      <>
                        <Download className="h-4 w-4 mr-2" />
                        Download Record
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      )}

      {/* Downloaded Record */}
      {hasDownloaded && downloadedRecord && (
        <div className="space-y-6">
          {/* Success Alert */}
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertTitle className="text-green-800">CKYC Record Downloaded Successfully</AlertTitle>
            <AlertDescription className="text-green-700">
              CKYC Number: {downloadedRecord.ckyc_number} | Last Updated:{' '}
              {formatDate(downloadedRecord.last_updated)}
            </AlertDescription>
          </Alert>

          {/* Record Details */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    {downloadedRecord.personal_details.title}{' '}
                    {downloadedRecord.personal_details.first_name}{' '}
                    {downloadedRecord.personal_details.last_name}
                  </CardTitle>
                  <CardDescription>CKYC: {downloadedRecord.ckyc_number}</CardDescription>
                </div>
                <Button onClick={handleSaveToEntity}>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Save to Entity
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="personal" className="space-y-4">
                <TabsList>
                  <TabsTrigger value="personal">Personal Details</TabsTrigger>
                  <TabsTrigger value="identity">Identity</TabsTrigger>
                  <TabsTrigger value="address">Address</TabsTrigger>
                  <TabsTrigger value="documents">Documents</TabsTrigger>
                </TabsList>

                <TabsContent value="personal" className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <Label className="text-xs text-muted-foreground">Full Name</Label>
                      <div className="font-medium">
                        {downloadedRecord.personal_details.title}{' '}
                        {downloadedRecord.personal_details.first_name}{' '}
                        {downloadedRecord.personal_details.middle_name}{' '}
                        {downloadedRecord.personal_details.last_name}
                      </div>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Date of Birth</Label>
                      <div className="font-medium">
                        {formatDate(downloadedRecord.personal_details.date_of_birth)}
                      </div>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Gender</Label>
                      <div className="font-medium">
                        {downloadedRecord.personal_details.gender}
                      </div>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Marital Status</Label>
                      <div className="font-medium">
                        {downloadedRecord.personal_details.marital_status}
                      </div>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Father's Name</Label>
                      <div className="font-medium">
                        {downloadedRecord.personal_details.father_name}
                      </div>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Mother's Name</Label>
                      <div className="font-medium">
                        {downloadedRecord.personal_details.mother_name}
                      </div>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Nationality</Label>
                      <div className="font-medium">
                        {downloadedRecord.personal_details.nationality}
                      </div>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Occupation</Label>
                      <div className="font-medium">
                        {downloadedRecord.personal_details.occupation}
                      </div>
                    </div>
                  </div>

                  <Separator />

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                      <Label className="text-xs text-muted-foreground">Mobile</Label>
                      <div className="font-medium">
                        {downloadedRecord.contact_details.mobile}
                      </div>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Email</Label>
                      <div className="font-medium">
                        {downloadedRecord.contact_details.email}
                      </div>
                    </div>
                    {downloadedRecord.contact_details.landline && (
                      <div>
                        <Label className="text-xs text-muted-foreground">Landline</Label>
                        <div className="font-medium">
                          {downloadedRecord.contact_details.landline}
                        </div>
                      </div>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="identity" className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                      <Label className="text-xs text-muted-foreground">PAN</Label>
                      <div className="font-medium">{downloadedRecord.identity_details.pan}</div>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Aadhaar (Masked)</Label>
                      <div className="font-medium">
                        {downloadedRecord.identity_details.aadhaar_masked}
                      </div>
                    </div>
                    {downloadedRecord.identity_details.passport && (
                      <div>
                        <Label className="text-xs text-muted-foreground">Passport</Label>
                        <div className="font-medium">
                          {downloadedRecord.identity_details.passport}
                        </div>
                      </div>
                    )}
                    {downloadedRecord.identity_details.voter_id && (
                      <div>
                        <Label className="text-xs text-muted-foreground">Voter ID</Label>
                        <div className="font-medium">
                          {downloadedRecord.identity_details.voter_id}
                        </div>
                      </div>
                    )}
                    {downloadedRecord.identity_details.driving_license && (
                      <div>
                        <Label className="text-xs text-muted-foreground">Driving License</Label>
                        <div className="font-medium">
                          {downloadedRecord.identity_details.driving_license}
                        </div>
                      </div>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="address" className="space-y-4">
                  {downloadedRecord.addresses.map((address, index) => (
                    <Card key={index}>
                      <CardContent className="pt-4">
                        <div className="flex items-start gap-3">
                          <MapPin className="h-5 w-5 text-muted-foreground mt-1" />
                          <div>
                            <div className="font-medium mb-2">
                              <Badge variant="outline">{address.type} Address</Badge>
                            </div>
                            <div>
                              {address.address_line1}
                              {address.address_line2 && `, ${address.address_line2}`}
                            </div>
                            <div>
                              {address.city}, {address.district}
                            </div>
                            <div>
                              {address.state} - {address.pincode}
                            </div>
                            <div>{address.country}</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </TabsContent>

                <TabsContent value="documents" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {downloadedRecord.documents.map((doc, index) => (
                      <Card key={index}>
                        <CardContent className="pt-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <FileText className="h-5 w-5 text-muted-foreground" />
                              <div>
                                <div className="font-medium">{doc.type}</div>
                                <div className="text-sm text-muted-foreground">{doc.number}</div>
                                {doc.expiry_date && (
                                  <div className="text-xs text-muted-foreground">
                                    Expires: {formatDate(doc.expiry_date)}
                                  </div>
                                )}
                              </div>
                            </div>
                            {doc.verified && (
                              <Badge variant="default" className="bg-green-600">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Verified
                              </Badge>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex gap-4 justify-end">
            <Button
              variant="outline"
              onClick={() => {
                setHasDownloaded(false);
                setDownloadedRecord(null);
              }}
            >
              Download Another
            </Button>
            <Button variant="outline">
              <Eye className="h-4 w-4 mr-2" />
              View PDF
            </Button>
            <Button onClick={handleSaveToEntity}>
              <CheckCircle className="h-4 w-4 mr-2" />
              Save to Entity
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

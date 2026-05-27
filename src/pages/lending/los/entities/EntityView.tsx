/**
 * Entity View Page
 * Read-only detail view of an entity with all related information
 */

import {
  Edit,
  FileText,
  Building2,
  Users,
  MapPin,
  Landmark,
  BarChart3,
  ShieldCheck,
  Star,
  MoreHorizontal,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { RatingBadge } from '@/components/lending/common/RatingBadge';
import { EntityStatusBadge, RiskCategoryBadge } from '@/components/lending/common/StatusBadge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/errorMessage';
import { logger } from '@/lib/logger';
import { entityApi } from '@/services/lending';
import type {
  Entity,
  EntityContact,
  EntityAddress,
  EntityBankAccount,
  EntityFinancial,
  EntityKYCDocument,
} from '@/types/lending';

const ENTITY_TYPE_LABELS: Record<string, string> = {
  CORPORATE: 'Corporate / Company',
  INDIVIDUAL: 'Individual',
  LLP: 'Limited Liability Partnership',
  PARTNERSHIP: 'Partnership Firm',
  TRUST: 'Trust',
};

export default function EntityView() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { id } = useParams<{ id: string }>();

  // State
  const [loading, setLoading] = useState(true);
  const [entity, setEntity] = useState<Entity | null>(null);
  const [contacts, setContacts] = useState<EntityContact[]>([]);
  const [addresses, setAddresses] = useState<EntityAddress[]>([]);
  const [bankAccounts, setBankAccounts] = useState<EntityBankAccount[]>([]);
  const [financials, setFinancials] = useState<EntityFinancial[]>([]);
  const [kycDocuments, setKycDocuments] = useState<EntityKYCDocument[]>([]);
  const [activeTab, setActiveTab] = useState('overview');

  // Load all entity data
  useEffect(() => {
    if (id) {
      loadEntityData(id);
    }
  }, [id]);

  const loadEntityData = async (entityId: string) => {
    setLoading(true);
    try {
      // Parallel fetch for performance
      const [entityData, contactsData, addressesData, bankData, financialsData, kycData] =
        await Promise.all([
          entityApi.getEntity(entityId),
          entityApi.getEntityContacts(entityId),
          entityApi.getEntityAddresses(entityId),
          entityApi.getEntityBankAccounts(entityId),
          entityApi.getEntityFinancials(entityId),
          entityApi.getEntityKYCDocuments(entityId),
        ]);

      setEntity(entityData);
      setContacts(contactsData);
      setAddresses(addressesData);
      setBankAccounts(bankData);
      setFinancials(financialsData);
      setKycDocuments(kycData);
    } catch (error) {
      logger.error('Failed to load entity data:', error);
      toast({
        title: 'Failed to load entity',
        description: getErrorMessage(error, 'Please try again.'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleInitiateRating = async () => {
    if (!id) return;
    try {
      await entityApi.initiateRating(id);
      toast({
        title: 'Rating initiated',
        description: 'Redirecting to the rating workflow.',
      });
      navigate(`/admin/lending/entities/${id}/rating`);
    } catch (error) {
      logger.error('Failed to initiate rating:', error);
      toast({
        title: 'Unable to initiate rating',
        description: getErrorMessage(error, 'Please try again.'),
        variant: 'destructive',
      });
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!entity) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-4">
        <p className="text-gray-500">Entity not found</p>
        <Button onClick={() => navigate('/admin/lending/entities')}>Back to Entities</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={entity.legalName}
        subtitle={`${entity.entityCode} | ${ENTITY_TYPE_LABELS[entity.entityType] || entity.entityType}`}
        breadcrumbs={[
          { label: 'Entities', to: '/admin/lending/entities' },
          { label: entity.entityCode },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <EntityStatusBadge status={entity.status} />
            <Button variant="outline" onClick={() => loadEntityData(id!)}>
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate(`/admin/lending/entities/${id}/edit`)}
            >
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleInitiateRating}>
                  <Star className="mr-2 h-4 w-4" />
                  Initiate Rating
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => navigate(`/admin/lending/applications/new?entityId=${id}`)}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  New Application
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <FileText className="mr-2 h-4 w-4" />
                  Download Profile
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-100 p-2">
                <ShieldCheck className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Internal Rating</p>
                <div className="mt-1">
                  {entity.internalRating ? (
                    <RatingBadge rating={entity.internalRating} size="lg" />
                  ) : (
                    <span className="text-gray-400">Not Rated</span>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-amber-100 p-2">
                <BarChart3 className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Risk Category</p>
                <div className="mt-1">
                  {entity.riskCategory ? (
                    <RiskCategoryBadge status={entity.riskCategory} />
                  ) : (
                    <span className="text-gray-400">Not Assessed</span>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-100 p-2">
                <Users className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Key Contacts</p>
                <p className="text-2xl font-semibold">{contacts.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-100 p-2">
                <FileText className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">KYC Documents</p>
                <p className="text-2xl font-semibold">
                  {kycDocuments.filter((d) => d.verificationStatus === 'VERIFIED').length}/
                  {kycDocuments.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <Building2 className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="contacts" className="gap-2">
            <Users className="h-4 w-4" />
            Contacts ({contacts.length})
          </TabsTrigger>
          <TabsTrigger value="addresses" className="gap-2">
            <MapPin className="h-4 w-4" />
            Addresses ({addresses.length})
          </TabsTrigger>
          <TabsTrigger value="bank" className="gap-2">
            <Landmark className="h-4 w-4" />
            Bank Accounts ({bankAccounts.length})
          </TabsTrigger>
          <TabsTrigger value="financials" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            Financials ({financials.length})
          </TabsTrigger>
          <TabsTrigger value="kyc" className="gap-2">
            <ShieldCheck className="h-4 w-4" />
            KYC ({kycDocuments.length})
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Entity Type</p>
                    <p className="font-medium">
                      {ENTITY_TYPE_LABELS[entity.entityType] || entity.entityType}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Entity Code</p>
                    <p className="font-mono font-medium">{entity.entityCode}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">PAN</p>
                    <p className="font-mono font-medium">{entity.pan}</p>
                  </div>
                  {entity.cin && (
                    <div>
                      <p className="text-sm text-gray-500">CIN / LLPIN</p>
                      <p className="font-mono font-medium">{entity.cin}</p>
                    </div>
                  )}
                  {entity.gstin && (
                    <div>
                      <p className="text-sm text-gray-500">GSTIN</p>
                      <p className="font-mono font-medium">{entity.gstin}</p>
                    </div>
                  )}
                  {entity.ckycNumber && (
                    <div>
                      <p className="text-sm text-gray-500">CKYC Number</p>
                      <p className="font-mono font-medium">{entity.ckycNumber}</p>
                    </div>
                  )}
                  {entity.dateOfIncorporation && (
                    <div>
                      <p className="text-sm text-gray-500">Date of Incorporation</p>
                      <p className="font-medium">
                        <DateDisplay date={entity.dateOfIncorporation} />
                      </p>
                    </div>
                  )}
                </div>

                {entity.remarks && (
                  <>
                    <Separator />
                    <div>
                      <p className="text-sm text-gray-500">Remarks</p>
                      <p className="mt-1 text-sm">{entity.remarks}</p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Audit Information */}
            <Card>
              <CardHeader>
                <CardTitle>Audit Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Created At</p>
                    <p className="font-medium">
                      <DateDisplay date={entity.createdAt} showTime />
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Last Updated</p>
                    <p className="font-medium">
                      <DateDisplay date={entity.updatedAt} showTime />
                    </p>
                  </div>
                  {entity.relationshipManagerId && (
                    <div className="col-span-2">
                      <p className="text-sm text-gray-500">Relationship Manager</p>
                      <p className="font-medium">{entity.relationshipManagerId}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Recent Financials Summary */}
            {financials.length > 0 && (
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Latest Financial Summary</CardTitle>
                  <CardDescription>Financial Year: {financials[0]?.financialYear}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
                    <div>
                      <p className="text-sm text-gray-500">Revenue</p>
                      <AmountDisplay
                        amount={financials[0]?.revenue || 0}
                        className="text-xl font-semibold"
                      />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Net Profit</p>
                      <AmountDisplay
                        amount={financials[0]?.netProfit || 0}
                        className="text-xl font-semibold"
                      />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Net Worth</p>
                      <AmountDisplay
                        amount={financials[0]?.netWorth || 0}
                        className="text-xl font-semibold"
                      />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Total Debt</p>
                      <AmountDisplay
                        amount={financials[0]?.totalDebt || 0}
                        className="text-xl font-semibold"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Contacts Tab */}
        <TabsContent value="contacts" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Contacts</CardTitle>
              <CardDescription>Directors, key persons, and authorized signatories</CardDescription>
            </CardHeader>
            <CardContent>
              {contacts.length === 0 ? (
                <p className="py-8 text-center text-gray-500">No contacts added yet</p>
              ) : (
                <div className="space-y-4">
                  {contacts.map((contact) => (
                    <div
                      key={contact.id}
                      className="flex items-start justify-between rounded-lg border p-4"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{contact.name}</p>
                          <Badge variant="outline">{contact.contactType}</Badge>
                          {contact.isPrimary && <Badge>Primary</Badge>}
                        </div>
                        {contact.designation && (
                          <p className="text-sm text-gray-500">{contact.designation}</p>
                        )}
                        <div className="mt-2 flex gap-4 text-sm text-gray-600">
                          {contact.email && <span>{contact.email}</span>}
                          {contact.phone && <span>{contact.phone}</span>}
                        </div>
                        {contact.din && (
                          <p className="mt-1 text-xs text-gray-400">DIN: {contact.din}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Addresses Tab */}
        <TabsContent value="addresses" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Addresses</CardTitle>
              <CardDescription>Registered, correspondence, and other addresses</CardDescription>
            </CardHeader>
            <CardContent>
              {addresses.length === 0 ? (
                <p className="py-8 text-center text-gray-500">No addresses added yet</p>
              ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {addresses.map((address) => (
                    <div key={address.id} className="rounded-lg border p-4">
                      <div className="mb-2 flex items-center gap-2">
                        <Badge variant="outline">{address.addressType}</Badge>
                        {address.isPrimary && <Badge>Primary</Badge>}
                      </div>
                      <p className="text-sm">
                        {address.addressLine1}
                        {address.addressLine2 && <>, {address.addressLine2}</>}
                      </p>
                      <p className="text-sm">
                        {address.city}, {address.state} - {address.pincode}
                      </p>
                      <p className="text-sm text-gray-500">{address.country}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Bank Accounts Tab */}
        <TabsContent value="bank" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Bank Accounts</CardTitle>
              <CardDescription>Bank accounts for disbursement and collection</CardDescription>
            </CardHeader>
            <CardContent>
              {bankAccounts.length === 0 ? (
                <p className="py-8 text-center text-gray-500">No bank accounts added yet</p>
              ) : (
                <div className="space-y-4">
                  {bankAccounts.map((account) => (
                    <div
                      key={account.id}
                      className="flex items-start justify-between rounded-lg border p-4"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{account.bankName}</p>
                          <Badge variant="outline">{account.accountType}</Badge>
                          {account.isPrimary && <Badge>Primary</Badge>}
                        </div>
                        <p className="mt-1 text-sm text-gray-600">A/C: {account.accountNumber}</p>
                        <p className="text-sm text-gray-600">
                          IFSC: {account.ifscCode} | Branch: {account.branchName}
                        </p>
                        {account.accountHolderName && (
                          <p className="text-sm text-gray-500">
                            Holder: {account.accountHolderName}
                          </p>
                        )}
                      </div>
                      <Badge variant={account.isVerified ? 'default' : 'secondary'}>
                        {account.isVerified ? 'Verified' : 'Pending'}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Financials Tab */}
        <TabsContent value="financials" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Financial Statements</CardTitle>
              <CardDescription>Annual financial data for analysis</CardDescription>
            </CardHeader>
            <CardContent>
              {financials.length === 0 ? (
                <p className="py-8 text-center text-gray-500">No financial data added yet</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="p-2 text-left">Financial Year</th>
                        <th className="p-2 text-right">Revenue</th>
                        <th className="p-2 text-right">EBITDA</th>
                        <th className="p-2 text-right">Net Profit</th>
                        <th className="p-2 text-right">Net Worth</th>
                        <th className="p-2 text-right">Total Debt</th>
                        <th className="p-2 text-left">Audited</th>
                      </tr>
                    </thead>
                    <tbody>
                      {financials.map((fin) => (
                        <tr key={fin.id} className="border-b">
                          <td className="p-2 font-medium">{fin.financialYear}</td>
                          <td className="p-2 text-right">
                            <AmountDisplay amount={fin.revenue || 0} />
                          </td>
                          <td className="p-2 text-right">
                            <AmountDisplay amount={fin.ebitda || 0} />
                          </td>
                          <td className="p-2 text-right">
                            <AmountDisplay amount={fin.netProfit || 0} />
                          </td>
                          <td className="p-2 text-right">
                            <AmountDisplay amount={fin.netWorth || 0} />
                          </td>
                          <td className="p-2 text-right">
                            <AmountDisplay amount={fin.totalDebt || 0} />
                          </td>
                          <td className="p-2">
                            <Badge variant={fin.isAudited ? 'default' : 'secondary'}>
                              {fin.isAudited ? 'Audited' : 'Provisional'}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* KYC Tab */}
        <TabsContent value="kyc" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>KYC Documents</CardTitle>
              <CardDescription>Identity and verification documents</CardDescription>
            </CardHeader>
            <CardContent>
              {kycDocuments.length === 0 ? (
                <p className="py-8 text-center text-gray-500">No KYC documents uploaded yet</p>
              ) : (
                <div className="space-y-4">
                  {kycDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-start justify-between rounded-lg border p-4"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-gray-400" />
                          <p className="font-medium">{doc.documentName || doc.documentTypeId}</p>
                        </div>
                        {doc.documentNumber && (
                          <p className="mt-1 text-sm text-gray-600">
                            Document No: {doc.documentNumber}
                          </p>
                        )}
                        {doc.expiryDate && (
                          <p className="text-sm text-gray-500">
                            Expiry: <DateDisplay date={doc.expiryDate} />
                          </p>
                        )}
                        <p className="mt-1 text-xs text-gray-400">
                          Uploaded: <DateDisplay date={doc.createdAt} showTime />
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            doc.verificationStatus === 'VERIFIED'
                              ? 'default'
                              : doc.verificationStatus === 'REJECTED'
                                ? 'destructive'
                                : 'secondary'
                          }
                        >
                          {doc.verificationStatus}
                        </Badge>
                        <Button variant="ghost" size="sm">
                          View
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

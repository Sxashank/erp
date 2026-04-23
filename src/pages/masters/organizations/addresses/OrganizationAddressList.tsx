import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Building2,
  Loader2,
  MapPin,
  MoreHorizontal,
  Plus,
  Star,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { organizationsApi } from '@/services/api';
import type { Organization, OrganizationAddress } from '@/types';

const ADDRESS_TYPE_LABELS: Record<string, string> = {
  REGISTERED: 'Registered Office',
  CORPORATE: 'Corporate Office',
  BRANCH: 'Branch Office',
  FACTORY: 'Factory/Plant',
  WAREHOUSE: 'Warehouse',
  OTHER: 'Other',
};

export function OrganizationAddressList() {
  const { orgId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [addresses, setAddresses] = useState<OrganizationAddress[]>([]);

  useEffect(() => {
    if (orgId) {
      fetchData();
    }
  }, [orgId]);

  const fetchData = async () => {
    if (!orgId) return;
    try {
      setLoading(true);
      const [orgRes, addrRes] = await Promise.all([
        organizationsApi.get(orgId),
        organizationsApi.listAddresses(orgId),
      ]);
      setOrganization(orgRes.data);
      setAddresses(addrRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSetPrimary = async (id: string) => {
    if (!orgId) return;
    try {
      await organizationsApi.setPrimaryAddress(orgId, id);
      fetchData();
    } catch (error) {
      console.error('Failed to set primary:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!orgId || !confirm('Are you sure you want to delete this address?')) return;
    try {
      await organizationsApi.deleteAddress(orgId, id);
      fetchData();
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/organizations')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Addresses</h1>
            <p className="text-sm text-slate-500">
              Manage addresses for {organization?.name}
            </p>
          </div>
        </div>
        <Button onClick={() => navigate(`/admin/organizations/${orgId}/addresses/new`)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Address
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            {organization?.name}
          </CardTitle>
          <CardDescription>
            {addresses.length} address{addresses.length !== 1 ? 'es' : ''} configured
          </CardDescription>
        </CardHeader>
        <CardContent>
          {addresses.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <MapPin className="h-12 w-12 text-slate-400" />
              <h3 className="mt-4 text-lg font-medium text-slate-900">No addresses</h3>
              <p className="mt-2 text-sm text-slate-500">
                Add addresses for your organization locations.
              </p>
              <Button
                className="mt-4"
                onClick={() => navigate(`/admin/organizations/${orgId}/addresses/new`)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Address
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Address</TableHead>
                  <TableHead>City</TableHead>
                  <TableHead>State</TableHead>
                  <TableHead>Pincode</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {addresses.map((address) => (
                  <TableRow key={address.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">
                          {ADDRESS_TYPE_LABELS[address.address_type] || address.address_type}
                        </Badge>
                        {address.is_primary && (
                          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div>{address.address_line1}</div>
                        {address.address_line2 && (
                          <div className="text-sm text-slate-500">{address.address_line2}</div>
                        )}
                        {address.landmark && (
                          <div className="text-xs text-slate-400">Near: {address.landmark}</div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{address.city}</TableCell>
                    <TableCell>{address.state_name || address.state_code}</TableCell>
                    <TableCell>{address.pincode}</TableCell>
                    <TableCell>
                      <Badge variant={address.status === 'ACTIVE' ? 'default' : 'secondary'}>
                        {address.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() =>
                              navigate(`/admin/organizations/${orgId}/addresses/${address.id}/edit`)
                            }
                          >
                            Edit
                          </DropdownMenuItem>
                          {!address.is_primary && (
                            <DropdownMenuItem onClick={() => handleSetPrimary(address.id)}>
                              Set as Primary
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => handleDelete(address.id)}
                          >
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

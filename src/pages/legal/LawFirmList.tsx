/**
 * Law Firm List Page
 * View and manage empanelled law firms
 */

import {
  Building,
  Plus,
  Search,
  MoreHorizontal,
  Edit,
  Trash2,
  Loader2,
  Phone,
  Mail,
  MapPin,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { Textarea } from '@/components/ui/textarea';
import { lawFirmApi } from '@/services/legalApi';
import type { LawFirm } from '@/types/legal';

import { logger } from "@/lib/logger";
export default function LawFirmList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [lawFirms, setLawFirms] = useState<LawFirm[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showDialog, setShowDialog] = useState(false);
  const [editingFirm, setEditingFirm] = useState<LawFirm | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    registration_number: '',
    bar_council_id: '',
    pan: '',
    gstin: '',
    address: '',
    city: '',
    state: '',
    pincode: '',
    phone: '',
    email: '',
    contact_person: '',
    fee_structure: '',
  });

  useEffect(() => {
    fetchLawFirms();
  }, [searchQuery]);

  const fetchLawFirms = async () => {
    try {
      const response = await lawFirmApi.getList({ search: searchQuery });
      setLawFirms(response.data.items);
    } catch (error) {
      logger.error('Failed to fetch law firms:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (firm?: LawFirm) => {
    if (firm) {
      setEditingFirm(firm);
      setFormData({
        name: firm.name,
        registration_number: firm.registration_number || '',
        bar_council_id: firm.bar_council_id || '',
        pan: firm.pan || '',
        gstin: firm.gstin || '',
        address: firm.address || '',
        city: firm.city || '',
        state: firm.state || '',
        pincode: firm.pincode || '',
        phone: firm.phone || '',
        email: firm.email || '',
        contact_person: firm.contact_person || '',
        fee_structure: firm.fee_structure || '',
      });
    } else {
      setEditingFirm(null);
      setFormData({
        name: '',
        registration_number: '',
        bar_council_id: '',
        pan: '',
        gstin: '',
        address: '',
        city: '',
        state: '',
        pincode: '',
        phone: '',
        email: '',
        contact_person: '',
        fee_structure: '',
      });
    }
    setShowDialog(true);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      if (editingFirm) {
        await lawFirmApi.update(editingFirm.id, formData);
      } else {
        await lawFirmApi.create(formData);
      }
      setShowDialog(false);
      fetchLawFirms();
    } catch (error) {
      logger.error('Failed to save law firm:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this law firm?')) return;

    try {
      await lawFirmApi.delete(id);
      fetchLawFirms();
    } catch (error) {
      logger.error('Failed to delete law firm:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Law Firms"
        subtitle="Manage empanelled law firms"
        actions={
          <Button onClick={() => handleOpenDialog()}>
            <Plus className="mr-2 h-4 w-4" />
            Add Law Firm
          </Button>
        }
      />

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Search law firms..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Law Firms Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Registration</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {lawFirms.map((firm) => (
                <TableRow key={firm.id}>
                  <TableCell>
                    <div>
                      <p className="font-medium">{firm.name}</p>
                      {firm.contact_person && (
                        <p className="text-sm text-gray-500">{firm.contact_person}</p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {firm.registration_number && <p>Reg: {firm.registration_number}</p>}
                      {firm.pan && <p>PAN: {firm.pan}</p>}
                      {firm.gstin && <p>GSTIN: {firm.gstin}</p>}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1 text-sm">
                      {firm.phone && (
                        <div className="flex items-center gap-1">
                          <Phone className="h-3 w-3 text-gray-400" />
                          {firm.phone}
                        </div>
                      )}
                      {firm.email && (
                        <div className="flex items-center gap-1">
                          <Mail className="h-3 w-3 text-gray-400" />
                          {firm.email}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm text-gray-500">
                      <MapPin className="h-3 w-3" />
                      {[firm.city, firm.state].filter(Boolean).join(', ') || '-'}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        firm.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                      }
                    >
                      {firm.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleOpenDialog(firm)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDelete(firm.id)}
                          className="text-red-600"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
              {lawFirms.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-gray-500">
                    <Building className="mx-auto mb-4 h-12 w-12 opacity-50" />
                    <p>No law firms found</p>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingFirm ? 'Edit Law Firm' : 'Add Law Firm'}</DialogTitle>
            <DialogDescription>
              {editingFirm ? 'Update law firm details' : 'Register a new empanelled law firm'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="col-span-2 space-y-2">
              <Label>Firm Name *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Enter law firm name"
              />
            </div>
            <div className="space-y-2">
              <Label>Registration Number</Label>
              <Input
                value={formData.registration_number}
                onChange={(e) => setFormData({ ...formData, registration_number: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Bar Council ID</Label>
              <Input
                value={formData.bar_council_id}
                onChange={(e) => setFormData({ ...formData, bar_council_id: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>PAN</Label>
              <Input
                value={formData.pan}
                onChange={(e) => setFormData({ ...formData, pan: e.target.value.toUpperCase() })}
                maxLength={10}
              />
            </div>
            <div className="space-y-2">
              <Label>GSTIN</Label>
              <Input
                value={formData.gstin}
                onChange={(e) => setFormData({ ...formData, gstin: e.target.value.toUpperCase() })}
                maxLength={15}
              />
            </div>
            <div className="space-y-2">
              <Label>Contact Person</Label>
              <Input
                value={formData.contact_person}
                onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Phone</Label>
              <Input
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Email</Label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Address</Label>
              <Textarea
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                rows={2}
              />
            </div>
            <div className="space-y-2">
              <Label>City</Label>
              <Input
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>State</Label>
              <Input
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Pincode</Label>
              <Input
                value={formData.pincode}
                onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
                maxLength={6}
              />
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Fee Structure</Label>
              <Textarea
                value={formData.fee_structure}
                onChange={(e) => setFormData({ ...formData, fee_structure: e.target.value })}
                placeholder="Describe the fee structure..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={!formData.name || submitting}>
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : editingFirm ? (
                'Update'
              ) : (
                'Create'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

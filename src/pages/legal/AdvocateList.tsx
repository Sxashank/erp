/**
 * Advocate List Page
 * View and manage empanelled advocates
 */

import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  User,
  Plus,
  Search,
  MoreHorizontal,
  Edit,
  Trash2,
  Loader2,
  Phone,
  Mail,
  Briefcase,
  Award,
} from 'lucide-react';
import { advocateApi, lawFirmApi } from '@/services/legalApi';
import type { Advocate, LawFirm } from '@/types/legal';

const indianStates = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
  'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
  'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
  'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Delhi',
];

const specializations = [
  'DRT', 'SARFAESI', 'NCLT', 'IBC', 'Banking Law', 'Civil Litigation',
  'Property Law', 'Arbitration', 'Consumer Law', 'Cheque Bounce (138 NI Act)',
];

export default function AdvocateList() {
  const [loading, setLoading] = useState(true);
  const [advocates, setAdvocates] = useState<Advocate[]>([]);
  const [lawFirms, setLawFirms] = useState<LawFirm[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterFirm, setFilterFirm] = useState('all');
  const [showDialog, setShowDialog] = useState(false);
  const [editingAdvocate, setEditingAdvocate] = useState<Advocate | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    law_firm_id: '',
    name: '',
    enrollment_number: '',
    bar_council_state: '',
    specializations: [] as string[],
    experience_years: '',
    mobile: '',
    email: '',
    fee_structure: '',
    is_empanelled: true,
  });

  useEffect(() => {
    fetchData();
  }, [searchQuery, filterFirm]);

  const fetchData = async () => {
    try {
      const [advocatesRes, firmsRes] = await Promise.all([
        advocateApi.getList({
          search: searchQuery,
          law_firm_id: filterFirm !== 'all' ? filterFirm : undefined,
        }),
        lawFirmApi.getList({ is_active: true }),
      ]);
      setAdvocates(advocatesRes.data);
      setLawFirms(firmsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (advocate?: Advocate) => {
    if (advocate) {
      setEditingAdvocate(advocate);
      setFormData({
        law_firm_id: advocate.law_firm_id || '',
        name: advocate.name,
        enrollment_number: advocate.enrollment_number,
        bar_council_state: advocate.bar_council_state,
        specializations: advocate.specializations || [],
        experience_years: advocate.experience_years?.toString() || '',
        mobile: advocate.mobile || '',
        email: advocate.email || '',
        fee_structure: advocate.fee_structure || '',
        is_empanelled: advocate.is_empanelled,
      });
    } else {
      setEditingAdvocate(null);
      setFormData({
        law_firm_id: '',
        name: '',
        enrollment_number: '',
        bar_council_state: '',
        specializations: [],
        experience_years: '',
        mobile: '',
        email: '',
        fee_structure: '',
        is_empanelled: true,
      });
    }
    setShowDialog(true);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const data = {
        ...formData,
        law_firm_id: formData.law_firm_id || undefined,
        experience_years: formData.experience_years
          ? parseInt(formData.experience_years)
          : undefined,
      };

      if (editingAdvocate) {
        await advocateApi.update(editingAdvocate.id, data);
      } else {
        await advocateApi.create(data);
      }
      setShowDialog(false);
      fetchData();
    } catch (error) {
      console.error('Failed to save advocate:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this advocate?')) return;

    try {
      await advocateApi.delete(id);
      fetchData();
    } catch (error) {
      console.error('Failed to delete advocate:', error);
    }
  };

  const toggleSpecialization = (spec: string) => {
    setFormData((prev) => ({
      ...prev,
      specializations: prev.specializations.includes(spec)
        ? prev.specializations.filter((s) => s !== spec)
        : [...prev.specializations, spec],
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Advocates"
        subtitle="Manage empanelled advocates"
        actions={
          <Button onClick={() => handleOpenDialog()}>
            <Plus className="h-4 w-4 mr-2" />
            Add Advocate
          </Button>
        }
      />

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search advocates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterFirm} onValueChange={setFilterFirm}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filter by firm" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Firms</SelectItem>
                {lawFirms.map((firm) => (
                  <SelectItem key={firm.id} value={firm.id}>
                    {firm.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Advocates Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Advocate</TableHead>
                <TableHead>Enrollment</TableHead>
                <TableHead>Law Firm</TableHead>
                <TableHead>Specializations</TableHead>
                <TableHead>Experience</TableHead>
                <TableHead>Cases</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {advocates.map((advocate) => (
                <TableRow key={advocate.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <User className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-medium">{advocate.name}</p>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          {advocate.mobile && (
                            <span className="flex items-center gap-1">
                              <Phone className="h-3 w-3" />
                              {advocate.mobile}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      <p>{advocate.enrollment_number}</p>
                      <p className="text-gray-500">{advocate.bar_council_state}</p>
                    </div>
                  </TableCell>
                  <TableCell>{advocate.law_firm_name || '-'}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {advocate.specializations?.slice(0, 2).map((spec) => (
                        <Badge key={spec} variant="secondary" className="text-xs">
                          {spec}
                        </Badge>
                      ))}
                      {advocate.specializations?.length > 2 && (
                        <Badge variant="secondary" className="text-xs">
                          +{advocate.specializations.length - 2}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {advocate.experience_years ? `${advocate.experience_years} years` : '-'}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Briefcase className="h-4 w-4 text-gray-400" />
                      <span>{advocate.cases_handled}</span>
                      {advocate.success_rate && (
                        <span className="text-green-600 text-sm">
                          ({advocate.success_rate}%)
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        advocate.is_empanelled
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }
                    >
                      {advocate.is_empanelled ? 'Empanelled' : 'Not Empanelled'}
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
                        <DropdownMenuItem onClick={() => handleOpenDialog(advocate)}>
                          <Edit className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDelete(advocate.id)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
              {advocates.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                    <User className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No advocates found</p>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingAdvocate ? 'Edit Advocate' : 'Add Advocate'}
            </DialogTitle>
            <DialogDescription>
              {editingAdvocate ? 'Update advocate details' : 'Register a new advocate'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="col-span-2 space-y-2">
              <Label>Full Name *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Enter advocate name"
              />
            </div>
            <div className="space-y-2">
              <Label>Enrollment Number *</Label>
              <Input
                value={formData.enrollment_number}
                onChange={(e) =>
                  setFormData({ ...formData, enrollment_number: e.target.value })
                }
                placeholder="e.g., MH/1234/2020"
              />
            </div>
            <div className="space-y-2">
              <Label>Bar Council State *</Label>
              <Select
                value={formData.bar_council_state}
                onValueChange={(v) => setFormData({ ...formData, bar_council_state: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select state" />
                </SelectTrigger>
                <SelectContent>
                  {indianStates.map((state) => (
                    <SelectItem key={state} value={state}>
                      {state}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Law Firm</Label>
              <Select
                value={formData.law_firm_id}
                onValueChange={(v) => setFormData({ ...formData, law_firm_id: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select law firm (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Independent</SelectItem>
                  {lawFirms.map((firm) => (
                    <SelectItem key={firm.id} value={firm.id}>
                      {firm.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Experience (Years)</Label>
              <Input
                type="number"
                value={formData.experience_years}
                onChange={(e) =>
                  setFormData({ ...formData, experience_years: e.target.value })
                }
                min="0"
              />
            </div>
            <div className="space-y-2">
              <Label>Mobile</Label>
              <Input
                value={formData.mobile}
                onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                maxLength={10}
              />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Specializations</Label>
              <div className="flex flex-wrap gap-2">
                {specializations.map((spec) => (
                  <Badge
                    key={spec}
                    variant={
                      formData.specializations.includes(spec) ? 'default' : 'outline'
                    }
                    className="cursor-pointer"
                    onClick={() => toggleSpecialization(spec)}
                  >
                    {spec}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Fee Structure</Label>
              <Textarea
                value={formData.fee_structure}
                onChange={(e) => setFormData({ ...formData, fee_structure: e.target.value })}
                placeholder="Describe fee structure..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={
                !formData.name ||
                !formData.enrollment_number ||
                !formData.bar_council_state ||
                submitting
              }
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : editingAdvocate ? (
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

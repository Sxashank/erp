import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { useForm } from 'react-hook-form';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

interface VerificationFormData {
  campaign_name: string;
  organization_id: string;
  location_id: string;
  department_id: string;
  category_id: string;
  start_date: string;
  end_date: string;
  description: string;
  verification_type: 'FULL' | 'PARTIAL' | 'RANDOM';
  sample_percentage?: number;
}

export function PhysicalVerificationForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [locations, setLocations] = useState<{ id: string; name: string }[]>([]);
  const [departments, setDepartments] = useState<{ id: string; name: string }[]>([]);
  const [categories, setCategories] = useState<{ id: string; name: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const isEditing = Boolean(id);

  const form = useForm<VerificationFormData>({
    defaultValues: {
      campaign_name: '',
      organization_id: '',
      location_id: '',
      department_id: '',
      category_id: '',
      start_date: '',
      end_date: '',
      description: '',
      verification_type: 'FULL',
      sample_percentage: 100,
    },
  });

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    const orgId = form.watch('organization_id');
    if (orgId) {
      fetchLocations(orgId);
      fetchDepartments(orgId);
      fetchCategories(orgId);
    }
  }, [form.watch('organization_id')]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0 && !form.getValues('organization_id')) {
        form.setValue('organization_id', data.items[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchLocations = async (orgId: string) => {
    // Mock data - replace with actual API call
    setLocations([
      { id: '1', name: 'Head Office' },
      { id: '2', name: 'Branch Office - Mumbai' },
      { id: '3', name: 'Branch Office - Delhi' },
    ]);
  };

  const fetchDepartments = async (orgId: string) => {
    // Mock data - replace with actual API call
    setDepartments([
      { id: '1', name: 'IT Department' },
      { id: '2', name: 'Finance' },
      { id: '3', name: 'Operations' },
      { id: '4', name: 'HR' },
    ]);
  };

  const fetchCategories = async (orgId: string) => {
    // Mock data - replace with actual API call
    setCategories([
      { id: '1', name: 'Computers & IT Equipment' },
      { id: '2', name: 'Furniture & Fixtures' },
      { id: '3', name: 'Office Equipment' },
      { id: '4', name: 'Vehicles' },
    ]);
  };

  const onSubmit = async (data: VerificationFormData) => {
    try {
      setLoading(true);
      // API call to create/update verification campaign
      toast({
        title: isEditing ? 'Campaign Updated' : 'Campaign Created',
        description: isEditing
          ? 'Verification campaign has been updated successfully.'
          : 'Verification campaign has been created successfully.',
      });
      navigate('/admin/fixed-assets/verification');
    } catch (error) {
      console.error('Failed to save campaign:', error);
      toast({
        title: 'Error',
        description: 'Failed to save verification campaign.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEditing ? 'Edit Verification Campaign' : 'New Verification Campaign'}
        subtitle={
          isEditing
            ? 'Update the verification campaign details'
            : 'Create a new physical verification campaign'
        }
        breadcrumbs={[
          { label: 'Physical Verification', to: '/admin/fixed-assets/verification' },
          { label: isEditing ? 'Edit' : 'New' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Campaign Details</CardTitle>
              <CardDescription>Basic information about the verification campaign</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="campaign_name"
                  rules={{ required: 'Campaign name is required' }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Campaign Name</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g., Q4 2024 Physical Verification" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="organization_id"
                  rules={{ required: 'Organization is required' }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Organization</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select organization" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {organizations.map((org) => (
                            <SelectItem key={org.id} value={org.id}>
                              {org.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="verification_type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Verification Type</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="FULL">Full Verification</SelectItem>
                          <SelectItem value="PARTIAL">Partial Verification</SelectItem>
                          <SelectItem value="RANDOM">Random Sampling</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        Full: All assets, Partial: Selected scope, Random: Sample-based
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {form.watch('verification_type') === 'RANDOM' && (
                  <FormField
                    control={form.control}
                    name="sample_percentage"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Sample Percentage</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={1}
                            max={100}
                            placeholder="e.g., 20"
                            {...field}
                            onChange={(e) => field.onChange(parseInt(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>Percentage of assets to verify</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                )}
              </div>

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Enter campaign description and objectives..."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Scope & Schedule</CardTitle>
              <CardDescription>Define the scope and timeline of the verification</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="location_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Location (Optional)</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="All locations" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="">All Locations</SelectItem>
                          {locations.map((loc) => (
                            <SelectItem key={loc.id} value={loc.id}>
                              {loc.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>Leave empty to include all locations</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="department_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Department (Optional)</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="All departments" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="">All Departments</SelectItem>
                          {departments.map((dept) => (
                            <SelectItem key={dept.id} value={dept.id}>
                              {dept.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>Leave empty to include all departments</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="category_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Asset Category (Optional)</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="All categories" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="">All Categories</SelectItem>
                          {categories.map((cat) => (
                            <SelectItem key={cat.id} value={cat.id}>
                              {cat.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>Leave empty to include all categories</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="start_date"
                  rules={{ required: 'Start date is required' }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Start Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="end_date"
                  rules={{ required: 'End date is required' }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>End Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/admin/fixed-assets/verification')}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              <Save className="mr-2 h-4 w-4" />
              {loading ? 'Saving...' : isEditing ? 'Update Campaign' : 'Create Campaign'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}

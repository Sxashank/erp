import { zodResolver } from '@hookform/resolvers/zod';
import { Calendar, Clock, GraduationCap, IndianRupee, MapPin, User, Users } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  useCreateTrainingProgram,
  useTrainingProgram,
  useUpdateTrainingProgram,
} from '@/hooks/hris/useTraining';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/errorMessage';

const trainingSchema = z.object({
  title: z.string().min(5, 'Title must be at least 5 characters'),
  description: z.string().min(20, 'Description must be at least 20 characters'),
  category: z.string().min(1, 'Category is required'),
  mode: z.enum(['CLASSROOM', 'VIRTUAL', 'E_LEARNING', 'WORKSHOP', 'ON_THE_JOB']),
  trainerType: z.enum(['INTERNAL', 'EXTERNAL']),
  trainerName: z.string().min(2, 'Trainer name is required'),
  trainerContact: z.string().optional(),
  startDate: z.string().min(1, 'Start date is required'),
  endDate: z.string().min(1, 'End date is required'),
  durationHours: z.coerce.number().min(1, 'Duration must be at least 1 hour'),
  location: z.string().min(1, 'Location is required'),
  maxParticipants: z.coerce.number().min(1, 'Max participants must be at least 1'),
  costPerParticipant: z.coerce.number().min(0),
  preRequisites: z.string().optional(),
  learningObjectives: z.string().optional(),
  isMandatory: z.boolean().default(false),
  certificateProvided: z.boolean().default(true),
});

type TrainingFormInput = z.input<typeof trainingSchema>;
type TrainingFormData = z.output<typeof trainingSchema>;

const DEFAULT_VALUES: TrainingFormInput = {
  title: '',
  description: '',
  category: '',
  mode: 'CLASSROOM',
  trainerType: 'INTERNAL',
  trainerName: '',
  trainerContact: '',
  startDate: '',
  endDate: '',
  durationHours: 8,
  location: '',
  maxParticipants: 25,
  costPerParticipant: 0,
  preRequisites: '',
  learningObjectives: '',
  isMandatory: false,
  certificateProvided: true,
};

export default function TrainingProgramForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const programQuery = useTrainingProgram(id);
  const createProgram = useCreateTrainingProgram();
  const updateProgram = useUpdateTrainingProgram(id ?? '');

  const form = useForm<TrainingFormInput, unknown, TrainingFormData>({
    resolver: zodResolver(trainingSchema),
    defaultValues: DEFAULT_VALUES,
  });

  useEffect(() => {
    if (!programQuery.data) {
      return;
    }
    form.reset({
      title: programQuery.data.title,
      description: programQuery.data.description,
      category: programQuery.data.category,
      mode: programQuery.data.mode,
      trainerType: programQuery.data.trainerType,
      trainerName: programQuery.data.trainerName,
      trainerContact: programQuery.data.trainerContact ?? '',
      startDate: programQuery.data.startDate,
      endDate: programQuery.data.endDate,
      durationHours: programQuery.data.durationHours,
      location: programQuery.data.location,
      maxParticipants: programQuery.data.maxParticipants,
      costPerParticipant: programQuery.data.costPerParticipant,
      preRequisites: programQuery.data.preRequisites ?? '',
      learningObjectives: programQuery.data.learningObjectives ?? '',
      isMandatory: programQuery.data.isMandatory,
      certificateProvided: programQuery.data.certificateProvided,
    });
  }, [form, programQuery.data]);

  const selectedMode = form.watch('mode');
  const trainerType = form.watch('trainerType');

  const onSubmit = async (data: TrainingFormData) => {
    try {
      if (isEdit && id) {
        await updateProgram.mutateAsync(data);
        toast({ title: 'Training program updated' });
      } else {
        const createdProgram = await createProgram.mutateAsync(data);
        toast({ title: 'Training program created' });
        navigate(`/admin/hris/training/${createdProgram.id}`);
        return;
      }
      navigate('/admin/hris/training');
    } catch (error: unknown) {
      toast({
        title: 'Unable to save training program',
        description: getErrorMessage(error, 'Please try again.'),
        variant: 'destructive',
      });
    }
  };

  if (isEdit && programQuery.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Edit Training Program"
          subtitle="Loading training program details"
          breadcrumbs={[
            { label: 'Training Programs', to: '/admin/hris/training' },
            { label: 'Edit' },
          ]}
        />
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Loading training program...
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isEdit && programQuery.isError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Edit Training Program"
          subtitle="Unable to load the selected program"
          breadcrumbs={[
            { label: 'Training Programs', to: '/admin/hris/training' },
            { label: 'Edit' },
          ]}
        />
        <ErrorState error={programQuery.error} onRetry={() => void programQuery.refetch()} />
      </div>
    );
  }

  const isSaving = createProgram.isPending || updateProgram.isPending;

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Training Program' : 'Create Training Program'}
        subtitle={isEdit ? 'Update program details' : 'Schedule a new training program'}
        breadcrumbs={[
          { label: 'Training Programs', to: '/admin/hris/training' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <GraduationCap className="h-5 w-5" />
                    Program Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="title"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Program Title</FormLabel>
                        <FormControl>
                          <Input placeholder="Enter program title" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Description</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="Describe the training program objectives and content..."
                            className="min-h-[100px]"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="category"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Category</FormLabel>
                          <Select value={field.value} onValueChange={field.onChange}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select category" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="Leadership">Leadership</SelectItem>
                              <SelectItem value="Technical">Technical</SelectItem>
                              <SelectItem value="Compliance">Compliance</SelectItem>
                              <SelectItem value="Soft Skills">Soft Skills</SelectItem>
                              <SelectItem value="Management">Management</SelectItem>
                              <SelectItem value="Sales">Sales</SelectItem>
                              <SelectItem value="Safety">Safety</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="mode"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Training Mode</FormLabel>
                          <Select value={field.value} onValueChange={field.onChange}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select mode" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="CLASSROOM">Classroom</SelectItem>
                              <SelectItem value="VIRTUAL">Virtual (Online)</SelectItem>
                              <SelectItem value="E_LEARNING">E-Learning</SelectItem>
                              <SelectItem value="WORKSHOP">Workshop</SelectItem>
                              <SelectItem value="ON_THE_JOB">On-the-Job</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="learningObjectives"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Learning Objectives</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="List the key learning objectives (one per line)..."
                            className="min-h-[80px]"
                            {...field}
                          />
                        </FormControl>
                        <FormDescription>
                          What participants will learn from this program
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="preRequisites"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Pre-requisites</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="Any pre-requisites for this training..."
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
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    Schedule & Location
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="startDate"
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
                      name="endDate"
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

                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="durationHours"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Duration (Hours)</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              min="1"
                              step="0.5"
                              value={typeof field.value === 'number' ? field.value : ''}
                              onChange={(event) => field.onChange(event.target.valueAsNumber)}
                              onBlur={field.onBlur}
                              name={field.name}
                              ref={field.ref}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="location"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>
                            {selectedMode === 'VIRTUAL' || selectedMode === 'E_LEARNING'
                              ? 'Meeting Link / Platform'
                              : 'Training Venue'}
                          </FormLabel>
                          <FormControl>
                            <Input
                              placeholder={
                                selectedMode === 'VIRTUAL' || selectedMode === 'E_LEARNING'
                                  ? 'Meeting link or platform'
                                  : 'Training venue'
                              }
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Trainer Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="trainerType"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Trainer Type</FormLabel>
                          <Select value={field.value} onValueChange={field.onChange}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select trainer type" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="INTERNAL">Internal</SelectItem>
                              <SelectItem value="EXTERNAL">External</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="trainerName"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>
                            {trainerType === 'INTERNAL'
                              ? 'Employee / Trainer Name'
                              : 'Trainer Name'}
                          </FormLabel>
                          <FormControl>
                            <Input placeholder="Trainer name" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="trainerContact"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Trainer Contact</FormLabel>
                        <FormControl>
                          <Input placeholder="Email or phone number" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Participation
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="maxParticipants"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Maximum Participants</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min="1"
                            value={typeof field.value === 'number' ? field.value : ''}
                            onChange={(event) => field.onChange(event.target.valueAsNumber)}
                            onBlur={field.onBlur}
                            name={field.name}
                            ref={field.ref}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="costPerParticipant"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Cost Per Participant</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min="0"
                            step="0.01"
                            value={typeof field.value === 'number' ? field.value : ''}
                            onChange={(event) => field.onChange(event.target.valueAsNumber)}
                            onBlur={field.onBlur}
                            name={field.name}
                            ref={field.ref}
                          />
                        </FormControl>
                        <FormDescription>Set to 0 for internal training</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Program Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="isMandatory"
                    render={({ field }) => (
                      <FormItem className="flex items-center justify-between rounded-lg border p-4">
                        <div className="space-y-1">
                          <FormLabel className="text-base">Mandatory Training</FormLabel>
                          <FormDescription>
                            Mark if attendance is compulsory for selected employees
                          </FormDescription>
                        </div>
                        <FormControl>
                          <Switch checked={field.value} onCheckedChange={field.onChange} />
                        </FormControl>
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="certificateProvided"
                    render={({ field }) => (
                      <FormItem className="flex items-center justify-between rounded-lg border p-4">
                        <div className="space-y-1">
                          <FormLabel className="text-base">Certificate Provided</FormLabel>
                          <FormDescription>
                            Enable if participants receive completion certificates
                          </FormDescription>
                        </div>
                        <FormControl>
                          <Switch checked={field.value} onCheckedChange={field.onChange} />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button type="submit" className="w-full" disabled={isSaving}>
                    {isSaving ? 'Saving...' : isEdit ? 'Update Program' : 'Create Program'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={() => navigate('/admin/hris/training')}
                    disabled={isSaving}
                  >
                    Cancel
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </form>
      </Form>
    </div>
  );
}

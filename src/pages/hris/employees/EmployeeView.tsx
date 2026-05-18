import {
  Briefcase,
  Building2,
  Calendar,
  Edit,
  FileText,
  GraduationCap,
  History,
  Home,
  Mail,
  Phone,
  User,
  Users,
  Wallet,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { hrisApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface Employee {
  id: string;
  employee_code: string;
  salutation?: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  full_name: string;
  date_of_birth?: string;
  gender?: string;
  blood_group?: string;
  marital_status?: string;
  wedding_anniversary?: string;
  nationality?: string;
  personal_email?: string;
  personal_mobile: string;
  alternate_mobile?: string;
  official_email?: string;
  official_mobile?: string;
  current_address_line1?: string;
  current_address_line2?: string;
  current_city?: string;
  current_state?: string;
  current_country?: string;
  current_pincode?: string;
  permanent_address_line1?: string;
  permanent_address_line2?: string;
  permanent_city?: string;
  permanent_state?: string;
  permanent_country?: string;
  permanent_pincode?: string;
  emergency_contact_name?: string;
  emergency_contact_relation?: string;
  emergency_contact_phone?: string;
  organization_id: string;
  organization_name?: string;
  department_id?: string;
  department_name?: string;
  designation_id?: string;
  designation_name?: string;
  reporting_manager_id?: string;
  reporting_manager_name?: string;
  employment_type: string;
  employment_status: string;
  date_of_joining: string;
  date_of_confirmation?: string;
  probation_end_date?: string;
  date_of_leaving?: string;
  leaving_reason?: string;
  notice_period_days?: number;
  shift_id?: string;
  shift_name?: string;
  work_location?: string;
  profile_photo_url?: string;
  remarks?: string;
  created_at: string;
  updated_at: string;
}

interface EmployeeDocument {
  id: string;
  document_type: string;
  document_number: string;
  issue_date?: string;
  expiry_date?: string;
  issuing_authority?: string;
  document_url?: string;
  is_verified: boolean;
}

interface EmployeeFamily {
  id: string;
  name: string;
  relation: string;
  date_of_birth?: string;
  occupation?: string;
  contact_number?: string;
  is_dependent: boolean;
  is_nominee: boolean;
  nominee_percentage?: number;
}

interface EmployeeBankAccount {
  id: string;
  bank_name: string;
  branch_name?: string;
  account_number: string;
  ifsc_code: string;
  account_type?: string;
  is_primary: boolean;
}

interface EmployeeEducation {
  id: string;
  education_level: string;
  degree_name: string;
  institution_name: string;
  university_board?: string;
  specialization?: string;
  start_year?: number;
  end_year?: number;
  percentage_cgpa?: number;
  is_highest_qualification: boolean;
}

interface EmployeeExperience {
  id: string;
  company_name: string;
  designation: string;
  department?: string;
  location?: string;
  from_date: string;
  to_date?: string;
  is_current: boolean;
  responsibilities?: string;
  leaving_reason?: string;
  last_ctc?: number;
}

interface EmployeeStatutory {
  id: string;
  pan_number?: string;
  aadhaar_number?: string;
  uan_number?: string;
  pf_number?: string;
  esi_number?: string;
  pf_joining_date?: string;
  is_pf_applicable: boolean;
  is_esi_applicable: boolean;
  is_pt_applicable: boolean;
  pt_state?: string;
}

interface LifecycleEvent {
  id: string;
  event_type: string;
  event_date: string;
  effective_date: string;
  description?: string;
  remarks?: string;
  created_at: string;
}

const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case 'ACTIVE':
      return 'bg-emerald-50 text-emerald-700';
    case 'PROBATION':
      return 'bg-amber-50 text-amber-700';
    case 'NOTICE_PERIOD':
      return 'bg-orange-50 text-orange-700';
    case 'RELIEVED':
      return 'bg-slate-100 text-slate-600';
    case 'SUSPENDED':
      return 'bg-red-50 text-red-700';
    default:
      return 'bg-slate-100 text-slate-600';
  }
};

export function EmployeeView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [documents, setDocuments] = useState<EmployeeDocument[]>([]);
  const [family, setFamily] = useState<EmployeeFamily[]>([]);
  const [bankAccounts, setBankAccounts] = useState<EmployeeBankAccount[]>([]);
  const [education, setEducation] = useState<EmployeeEducation[]>([]);
  const [experience, setExperience] = useState<EmployeeExperience[]>([]);
  const [statutory, setStatutory] = useState<EmployeeStatutory | null>(null);
  const [lifecycle, setLifecycle] = useState<LifecycleEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEmployeeData = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const [empRes, docsRes, familyRes, bankRes, eduRes, expRes, statRes, lifecycleRes] =
          await Promise.all([
            hrisApi.getEmployee(id),
            hrisApi.listEmployeeDocuments(id),
            hrisApi.listEmployeeFamily(id),
            hrisApi.listEmployeeBankAccounts(id),
            hrisApi.listEmployeeEducation(id),
            hrisApi.listEmployeeExperience(id),
            hrisApi.getEmployeeStatutory(id).catch(() => ({ data: null })),
            hrisApi.listEmployeeLifecycle(id),
          ]);

        setEmployee(empRes.data);
        setDocuments(docsRes.data.items || docsRes.data || []);
        setFamily(familyRes.data.items || familyRes.data || []);
        setBankAccounts(bankRes.data.items || bankRes.data || []);
        setEducation(eduRes.data.items || eduRes.data || []);
        setExperience(expRes.data.items || expRes.data || []);
        setStatutory(statRes.data);
        setLifecycle(lifecycleRes.data.items || lifecycleRes.data || []);
      } catch (error) {
        logger.error('Failed to fetch employee data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEmployeeData();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-sm text-slate-500">Loading...</p>
      </div>
    );
  }

  if (!employee) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-sm text-slate-500">Employee not found</p>
        <Button variant="link" onClick={() => navigate('/admin/hris/employees')}>
          Back to Employee List
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={employee.full_name}
        subtitle={`${employee.employee_code} • ${employee.designation_name || 'No Designation'}`}
        breadcrumbs={[
          { label: 'Employees', to: '/admin/hris/employees' },
          { label: employee.employee_code },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Badge className={getStatusBadgeColor(employee.employment_status)}>
              {employee.employment_status}
            </Badge>
            <Button onClick={() => navigate(`/admin/hris/employees/${id}/edit`)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          </div>
        }
      />

      {/* Quick Info Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-6 md:grid-cols-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-50">
                <Building2 className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Department</p>
                <p className="font-medium">{employee.department_name || '-'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-50">
                <Calendar className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Joining Date</p>
                <p className="font-medium">
                  <DateDisplay date={employee.date_of_joining} />
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-50">
                <Phone className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Mobile</p>
                <p className="font-medium">{employee.personal_mobile}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-50">
                <Mail className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Email</p>
                <p className="font-medium">
                  {employee.official_email || employee.personal_email || '-'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="personal" className="space-y-4">
        <TabsList>
          <TabsTrigger value="personal">
            <User className="mr-2 h-4 w-4" />
            Personal
          </TabsTrigger>
          <TabsTrigger value="employment">
            <Briefcase className="mr-2 h-4 w-4" />
            Employment
          </TabsTrigger>
          <TabsTrigger value="documents">
            <FileText className="mr-2 h-4 w-4" />
            Documents
          </TabsTrigger>
          <TabsTrigger value="family">
            <Users className="mr-2 h-4 w-4" />
            Family
          </TabsTrigger>
          <TabsTrigger value="education">
            <GraduationCap className="mr-2 h-4 w-4" />
            Education
          </TabsTrigger>
          <TabsTrigger value="experience">
            <Briefcase className="mr-2 h-4 w-4" />
            Experience
          </TabsTrigger>
          <TabsTrigger value="bank">
            <Wallet className="mr-2 h-4 w-4" />
            Bank
          </TabsTrigger>
          <TabsTrigger value="statutory">
            <FileText className="mr-2 h-4 w-4" />
            Statutory
          </TabsTrigger>
          <TabsTrigger value="lifecycle">
            <History className="mr-2 h-4 w-4" />
            History
          </TabsTrigger>
        </TabsList>

        {/* Personal Tab */}
        <TabsContent value="personal">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Personal Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <h4 className="font-medium text-slate-900">Basic Details</h4>
                  <div className="grid gap-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Full Name</span>
                      <span className="font-medium">{employee.full_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Date of Birth</span>
                      <DateDisplay date={employee.date_of_birth} className="font-medium" />
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Gender</span>
                      <span className="font-medium">{employee.gender || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Blood Group</span>
                      <span className="font-medium">{employee.blood_group || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Marital Status</span>
                      <span className="font-medium">{employee.marital_status || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Nationality</span>
                      <span className="font-medium">{employee.nationality || '-'}</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <h4 className="font-medium text-slate-900">Contact Details</h4>
                  <div className="grid gap-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Personal Email</span>
                      <span className="font-medium">{employee.personal_email || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Personal Mobile</span>
                      <span className="font-medium">{employee.personal_mobile}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Alternate Mobile</span>
                      <span className="font-medium">{employee.alternate_mobile || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Emergency Contact</span>
                      <span className="font-medium">{employee.emergency_contact_name || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Emergency Phone</span>
                      <span className="font-medium">{employee.emergency_contact_phone || '-'}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 grid gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <h4 className="flex items-center gap-2 font-medium text-slate-900">
                    <Home className="h-4 w-4" />
                    Current Address
                  </h4>
                  <p className="text-sm text-slate-600">
                    {employee.current_address_line1 || '-'}
                    {employee.current_address_line2 && (
                      <>
                        <br />
                        {employee.current_address_line2}
                      </>
                    )}
                    {employee.current_city && (
                      <>
                        <br />
                        {employee.current_city}
                      </>
                    )}
                    {employee.current_state && <>, {employee.current_state}</>}
                    {employee.current_pincode && <> - {employee.current_pincode}</>}
                    {employee.current_country && (
                      <>
                        <br />
                        {employee.current_country}
                      </>
                    )}
                  </p>
                </div>
                <div className="space-y-4">
                  <h4 className="flex items-center gap-2 font-medium text-slate-900">
                    <Home className="h-4 w-4" />
                    Permanent Address
                  </h4>
                  <p className="text-sm text-slate-600">
                    {employee.permanent_address_line1 || '-'}
                    {employee.permanent_address_line2 && (
                      <>
                        <br />
                        {employee.permanent_address_line2}
                      </>
                    )}
                    {employee.permanent_city && (
                      <>
                        <br />
                        {employee.permanent_city}
                      </>
                    )}
                    {employee.permanent_state && <>, {employee.permanent_state}</>}
                    {employee.permanent_pincode && <> - {employee.permanent_pincode}</>}
                    {employee.permanent_country && (
                      <>
                        <br />
                        {employee.permanent_country}
                      </>
                    )}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Employment Tab */}
        <TabsContent value="employment">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="h-5 w-5" />
                Employment Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <h4 className="font-medium text-slate-900">Position</h4>
                  <div className="grid gap-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Organization</span>
                      <span className="font-medium">{employee.organization_name || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Department</span>
                      <span className="font-medium">{employee.department_name || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Designation</span>
                      <span className="font-medium">{employee.designation_name || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Reporting Manager</span>
                      <span className="font-medium">{employee.reporting_manager_name || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Work Location</span>
                      <span className="font-medium">{employee.work_location || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Shift</span>
                      <span className="font-medium">{employee.shift_name || '-'}</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <h4 className="font-medium text-slate-900">Employment</h4>
                  <div className="grid gap-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Employee Code</span>
                      <span className="font-medium">{employee.employee_code}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Employment Type</span>
                      <Badge variant="outline">{employee.employment_type}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Employment Status</span>
                      <Badge className={getStatusBadgeColor(employee.employment_status)}>
                        {employee.employment_status}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Date of Joining</span>
                      <DateDisplay date={employee.date_of_joining} className="font-medium" />
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Confirmation Date</span>
                      <DateDisplay date={employee.date_of_confirmation} className="font-medium" />
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Notice Period (Days)</span>
                      <span className="font-medium">{employee.notice_period_days || '-'}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                <h4 className="font-medium text-slate-900">Official Contact</h4>
                <div className="grid gap-3 text-sm md:grid-cols-2">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Official Email</span>
                    <span className="font-medium">{employee.official_email || '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Official Mobile</span>
                    <span className="font-medium">{employee.official_mobile || '-'}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Documents ({documents.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {documents.length === 0 ? (
                <p className="py-8 text-center text-sm text-slate-500">No documents uploaded</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Document Type</TableHead>
                      <TableHead>Number</TableHead>
                      <TableHead>Issue Date</TableHead>
                      <TableHead>Expiry Date</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {documents.map((doc) => (
                      <TableRow key={doc.id}>
                        <TableCell className="font-medium">{doc.document_type}</TableCell>
                        <TableCell>{doc.document_number}</TableCell>
                        <TableCell>
                          <DateDisplay date={doc.issue_date} />
                        </TableCell>
                        <TableCell>
                          <DateDisplay date={doc.expiry_date} />
                        </TableCell>
                        <TableCell>
                          <Badge variant={doc.is_verified ? 'default' : 'secondary'}>
                            {doc.is_verified ? 'Verified' : 'Pending'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Family Tab */}
        <TabsContent value="family">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Family Members ({family.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {family.length === 0 ? (
                <p className="py-8 text-center text-sm text-slate-500">No family members added</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Relation</TableHead>
                      <TableHead>Date of Birth</TableHead>
                      <TableHead>Contact</TableHead>
                      <TableHead>Dependent</TableHead>
                      <TableHead>Nominee</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {family.map((member) => (
                      <TableRow key={member.id}>
                        <TableCell className="font-medium">{member.name}</TableCell>
                        <TableCell>{member.relation}</TableCell>
                        <TableCell>
                          <DateDisplay date={member.date_of_birth} />
                        </TableCell>
                        <TableCell>{member.contact_number || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={member.is_dependent ? 'default' : 'secondary'}>
                            {member.is_dependent ? 'Yes' : 'No'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {member.is_nominee ? (
                            <Badge variant="default">{member.nominee_percentage}%</Badge>
                          ) : (
                            <Badge variant="secondary">No</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Education Tab */}
        <TabsContent value="education">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GraduationCap className="h-5 w-5" />
                Education ({education.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {education.length === 0 ? (
                <p className="py-8 text-center text-sm text-slate-500">
                  No education records added
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Level</TableHead>
                      <TableHead>Degree</TableHead>
                      <TableHead>Institution</TableHead>
                      <TableHead>Specialization</TableHead>
                      <TableHead>Year</TableHead>
                      <TableHead>Score</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {education.map((edu) => (
                      <TableRow key={edu.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {edu.education_level}
                            {edu.is_highest_qualification && (
                              <Badge variant="outline" className="text-xs">
                                Highest
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="font-medium">{edu.degree_name}</TableCell>
                        <TableCell>{edu.institution_name}</TableCell>
                        <TableCell>{edu.specialization || '-'}</TableCell>
                        <TableCell>
                          {edu.start_year && edu.end_year
                            ? `${edu.start_year} - ${edu.end_year}`
                            : '-'}
                        </TableCell>
                        <TableCell>
                          {edu.percentage_cgpa ? `${edu.percentage_cgpa}%` : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Experience Tab */}
        <TabsContent value="experience">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="h-5 w-5" />
                Work Experience ({experience.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {experience.length === 0 ? (
                <p className="py-8 text-center text-sm text-slate-500">
                  No experience records added
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Company</TableHead>
                      <TableHead>Designation</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Last CTC</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {experience.map((exp) => (
                      <TableRow key={exp.id}>
                        <TableCell className="font-medium">{exp.company_name}</TableCell>
                        <TableCell>{exp.designation}</TableCell>
                        <TableCell>{exp.department || '-'}</TableCell>
                        <TableCell>
                          <DateDisplay date={exp.from_date} /> - {exp.is_current ? 'Present' : <DateDisplay date={exp.to_date} />}
                        </TableCell>
                        <TableCell>
                          {exp.last_ctc ? `₹${exp.last_ctc.toLocaleString()}` : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Bank Tab */}
        <TabsContent value="bank">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wallet className="h-5 w-5" />
                Bank Accounts ({bankAccounts.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {bankAccounts.length === 0 ? (
                <p className="py-8 text-center text-sm text-slate-500">No bank accounts added</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Bank Name</TableHead>
                      <TableHead>Branch</TableHead>
                      <TableHead>Account Number</TableHead>
                      <TableHead>IFSC Code</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Primary</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {bankAccounts.map((account) => (
                      <TableRow key={account.id}>
                        <TableCell className="font-medium">{account.bank_name}</TableCell>
                        <TableCell>{account.branch_name || '-'}</TableCell>
                        <TableCell>{account.account_number}</TableCell>
                        <TableCell>{account.ifsc_code}</TableCell>
                        <TableCell>{account.account_type || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={account.is_primary ? 'default' : 'secondary'}>
                            {account.is_primary ? 'Primary' : 'Secondary'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Statutory Tab */}
        <TabsContent value="statutory">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Statutory Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!statutory ? (
                <p className="py-8 text-center text-sm text-slate-500">
                  No statutory information added
                </p>
              ) : (
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="space-y-4">
                    <h4 className="font-medium text-slate-900">Identity</h4>
                    <div className="grid gap-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-500">PAN Number</span>
                        <span className="font-medium">{statutory.pan_number || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Aadhaar Number</span>
                        <span className="font-medium">{statutory.aadhaar_number || '-'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h4 className="font-medium text-slate-900">PF & ESI</h4>
                    <div className="grid gap-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-500">UAN Number</span>
                        <span className="font-medium">{statutory.uan_number || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">PF Number</span>
                        <span className="font-medium">{statutory.pf_number || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">PF Applicable</span>
                        <Badge variant={statutory.is_pf_applicable ? 'default' : 'secondary'}>
                          {statutory.is_pf_applicable ? 'Yes' : 'No'}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">ESI Number</span>
                        <span className="font-medium">{statutory.esi_number || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">ESI Applicable</span>
                        <Badge variant={statutory.is_esi_applicable ? 'default' : 'secondary'}>
                          {statutory.is_esi_applicable ? 'Yes' : 'No'}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">PT Applicable</span>
                        <Badge variant={statutory.is_pt_applicable ? 'default' : 'secondary'}>
                          {statutory.is_pt_applicable ? 'Yes' : 'No'}
                        </Badge>
                      </div>
                      {statutory.pt_state && (
                        <div className="flex justify-between">
                          <span className="text-slate-500">PT State</span>
                          <span className="font-medium">{statutory.pt_state}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Lifecycle Tab */}
        <TabsContent value="lifecycle">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Employment History ({lifecycle.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {lifecycle.length === 0 ? (
                <p className="py-8 text-center text-sm text-slate-500">
                  No lifecycle events recorded
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Event Type</TableHead>
                      <TableHead>Event Date</TableHead>
                      <TableHead>Effective Date</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Remarks</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {lifecycle.map((event) => (
                      <TableRow key={event.id}>
                        <TableCell>
                          <Badge variant="outline">{event.event_type}</Badge>
                        </TableCell>
                        <TableCell><DateDisplay date={event.event_date} /></TableCell>
                        <TableCell><DateDisplay date={event.effective_date} /></TableCell>
                        <TableCell>{event.description || '-'}</TableCell>
                        <TableCell>{event.remarks || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

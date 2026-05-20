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
  employeeCode: string;
  salutation?: string;
  firstName: string;
  middleName?: string;
  lastName: string;
  fullName: string;
  dateOfBirth?: string;
  gender?: string;
  bloodGroup?: string;
  maritalStatus?: string;
  weddingAnniversary?: string;
  nationality?: string;
  personalEmail?: string;
  personalMobile: string;
  alternateMobile?: string;
  officialEmail?: string;
  officialMobile?: string;
  currentAddressLine1?: string;
  currentAddressLine2?: string;
  currentCity?: string;
  currentState?: string;
  currentCountry?: string;
  currentPincode?: string;
  permanentAddressLine1?: string;
  permanentAddressLine2?: string;
  permanentCity?: string;
  permanentState?: string;
  permanentCountry?: string;
  permanentPincode?: string;
  emergencyContactName?: string;
  emergencyContactRelation?: string;
  emergencyContactPhone?: string;
  organizationId: string;
  organizationName?: string;
  departmentId?: string;
  departmentName?: string;
  designationId?: string;
  designationName?: string;
  reportingManagerId?: string;
  reportingManagerName?: string;
  employmentType: string;
  employmentStatus: string;
  dateOfJoining: string;
  dateOfConfirmation?: string;
  probationEndDate?: string;
  dateOfLeaving?: string;
  leavingReason?: string;
  noticePeriodDays?: number;
  shiftId?: string;
  shiftName?: string;
  workLocation?: string;
  profilePhotoUrl?: string;
  remarks?: string;
  createdAt: string;
  updatedAt: string;
}

interface EmployeeDocument {
  id: string;
  documentType: string;
  documentNumber: string;
  issueDate?: string;
  expiryDate?: string;
  issuingAuthority?: string;
  documentUrl?: string;
  isVerified: boolean;
}

interface EmployeeFamily {
  id: string;
  name: string;
  relation: string;
  dateOfBirth?: string;
  occupation?: string;
  contactNumber?: string;
  isDependent: boolean;
  isNominee: boolean;
  nomineePercentage?: number;
}

interface EmployeeBankAccount {
  id: string;
  bankName: string;
  branchName?: string;
  accountNumber: string;
  ifscCode: string;
  accountType?: string;
  isPrimary: boolean;
}

interface EmployeeEducation {
  id: string;
  educationLevel: string;
  degreeName: string;
  institutionName: string;
  universityBoard?: string;
  specialization?: string;
  startYear?: number;
  endYear?: number;
  percentageCgpa?: number;
  isHighestQualification: boolean;
}

interface EmployeeExperience {
  id: string;
  companyName: string;
  designation: string;
  department?: string;
  location?: string;
  fromDate: string;
  toDate?: string;
  isCurrent: boolean;
  responsibilities?: string;
  leavingReason?: string;
  lastCtc?: number;
}

interface EmployeeStatutory {
  id: string;
  panNumber?: string;
  aadhaarNumber?: string;
  uanNumber?: string;
  pfNumber?: string;
  esiNumber?: string;
  pfJoiningDate?: string;
  isPfApplicable: boolean;
  isEsiApplicable: boolean;
  isPtApplicable: boolean;
  ptState?: string;
}

interface LifecycleEvent {
  id: string;
  eventType: string;
  eventDate: string;
  effectiveDate: string;
  description?: string;
  remarks?: string;
  createdAt: string;
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
        title={employee.fullName}
        subtitle={`${employee.employeeCode} • ${employee.designationName || 'No Designation'}`}
        breadcrumbs={[
          { label: 'Employees', to: '/admin/hris/employees' },
          { label: employee.employeeCode },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Badge className={getStatusBadgeColor(employee.employmentStatus)}>
              {employee.employmentStatus}
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
                <p className="font-medium">{employee.departmentName || '-'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-50">
                <Calendar className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Joining Date</p>
                <p className="font-medium">
                  <DateDisplay date={employee.dateOfJoining} />
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-50">
                <Phone className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Mobile</p>
                <p className="font-medium">{employee.personalMobile}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-50">
                <Mail className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Email</p>
                <p className="font-medium">
                  {employee.officialEmail || employee.personalEmail || '-'}
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
                      <span className="font-medium">{employee.fullName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Date of Birth</span>
                      <DateDisplay date={employee.dateOfBirth} className="font-medium" />
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Gender</span>
                      <span className="font-medium">{employee.gender || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Blood Group</span>
                      <span className="font-medium">{employee.bloodGroup || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Marital Status</span>
                      <span className="font-medium">{employee.maritalStatus || '-'}</span>
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
                      <span className="font-medium">{employee.personalEmail || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Personal Mobile</span>
                      <span className="font-medium">{employee.personalMobile}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Alternate Mobile</span>
                      <span className="font-medium">{employee.alternateMobile || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Emergency Contact</span>
                      <span className="font-medium">{employee.emergencyContactName || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Emergency Phone</span>
                      <span className="font-medium">{employee.emergencyContactPhone || '-'}</span>
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
                    {employee.currentAddressLine1 || '-'}
                    {employee.currentAddressLine2 && (
                      <>
                        <br />
                        {employee.currentAddressLine2}
                      </>
                    )}
                    {employee.currentCity && (
                      <>
                        <br />
                        {employee.currentCity}
                      </>
                    )}
                    {employee.currentState && <>, {employee.currentState}</>}
                    {employee.currentPincode && <> - {employee.currentPincode}</>}
                    {employee.currentCountry && (
                      <>
                        <br />
                        {employee.currentCountry}
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
                    {employee.permanentAddressLine1 || '-'}
                    {employee.permanentAddressLine2 && (
                      <>
                        <br />
                        {employee.permanentAddressLine2}
                      </>
                    )}
                    {employee.permanentCity && (
                      <>
                        <br />
                        {employee.permanentCity}
                      </>
                    )}
                    {employee.permanentState && <>, {employee.permanentState}</>}
                    {employee.permanentPincode && <> - {employee.permanentPincode}</>}
                    {employee.permanentCountry && (
                      <>
                        <br />
                        {employee.permanentCountry}
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
                      <span className="font-medium">{employee.organizationName || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Department</span>
                      <span className="font-medium">{employee.departmentName || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Designation</span>
                      <span className="font-medium">{employee.designationName || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Reporting Manager</span>
                      <span className="font-medium">{employee.reportingManagerName || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Work Location</span>
                      <span className="font-medium">{employee.workLocation || '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Shift</span>
                      <span className="font-medium">{employee.shiftName || '-'}</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <h4 className="font-medium text-slate-900">Employment</h4>
                  <div className="grid gap-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Employee Code</span>
                      <span className="font-medium">{employee.employeeCode}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Employment Type</span>
                      <Badge variant="outline">{employee.employmentType}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Employment Status</span>
                      <Badge className={getStatusBadgeColor(employee.employmentStatus)}>
                        {employee.employmentStatus}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Date of Joining</span>
                      <DateDisplay date={employee.dateOfJoining} className="font-medium" />
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Confirmation Date</span>
                      <DateDisplay date={employee.dateOfConfirmation} className="font-medium" />
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Notice Period (Days)</span>
                      <span className="font-medium">{employee.noticePeriodDays || '-'}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                <h4 className="font-medium text-slate-900">Official Contact</h4>
                <div className="grid gap-3 text-sm md:grid-cols-2">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Official Email</span>
                    <span className="font-medium">{employee.officialEmail || '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Official Mobile</span>
                    <span className="font-medium">{employee.officialMobile || '-'}</span>
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
                        <TableCell className="font-medium">{doc.documentType}</TableCell>
                        <TableCell>{doc.documentNumber}</TableCell>
                        <TableCell>
                          <DateDisplay date={doc.issueDate} />
                        </TableCell>
                        <TableCell>
                          <DateDisplay date={doc.expiryDate} />
                        </TableCell>
                        <TableCell>
                          <Badge variant={doc.isVerified ? 'default' : 'secondary'}>
                            {doc.isVerified ? 'Verified' : 'Pending'}
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
                          <DateDisplay date={member.dateOfBirth} />
                        </TableCell>
                        <TableCell>{member.contactNumber || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={member.isDependent ? 'default' : 'secondary'}>
                            {member.isDependent ? 'Yes' : 'No'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {member.isNominee ? (
                            <Badge variant="default">{member.nomineePercentage}%</Badge>
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
                            {edu.educationLevel}
                            {edu.isHighestQualification && (
                              <Badge variant="outline" className="text-xs">
                                Highest
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="font-medium">{edu.degreeName}</TableCell>
                        <TableCell>{edu.institutionName}</TableCell>
                        <TableCell>{edu.specialization || '-'}</TableCell>
                        <TableCell>
                          {edu.startYear && edu.endYear
                            ? `${edu.startYear} - ${edu.endYear}`
                            : '-'}
                        </TableCell>
                        <TableCell>
                          {edu.percentageCgpa ? `${edu.percentageCgpa}%` : '-'}
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
                        <TableCell className="font-medium">{exp.companyName}</TableCell>
                        <TableCell>{exp.designation}</TableCell>
                        <TableCell>{exp.department || '-'}</TableCell>
                        <TableCell>
                          <DateDisplay date={exp.fromDate} /> - {exp.isCurrent ? 'Present' : <DateDisplay date={exp.toDate} />}
                        </TableCell>
                        <TableCell>
                          {exp.lastCtc ? `₹${exp.lastCtc.toLocaleString()}` : '-'}
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
                        <TableCell className="font-medium">{account.bankName}</TableCell>
                        <TableCell>{account.branchName || '-'}</TableCell>
                        <TableCell>{account.accountNumber}</TableCell>
                        <TableCell>{account.ifscCode}</TableCell>
                        <TableCell>{account.accountType || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={account.isPrimary ? 'default' : 'secondary'}>
                            {account.isPrimary ? 'Primary' : 'Secondary'}
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
                        <span className="font-medium">{statutory.panNumber || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Aadhaar Number</span>
                        <span className="font-medium">{statutory.aadhaarNumber || '-'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h4 className="font-medium text-slate-900">PF & ESI</h4>
                    <div className="grid gap-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-500">UAN Number</span>
                        <span className="font-medium">{statutory.uanNumber || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">PF Number</span>
                        <span className="font-medium">{statutory.pfNumber || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">PF Applicable</span>
                        <Badge variant={statutory.isPfApplicable ? 'default' : 'secondary'}>
                          {statutory.isPfApplicable ? 'Yes' : 'No'}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">ESI Number</span>
                        <span className="font-medium">{statutory.esiNumber || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">ESI Applicable</span>
                        <Badge variant={statutory.isEsiApplicable ? 'default' : 'secondary'}>
                          {statutory.isEsiApplicable ? 'Yes' : 'No'}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">PT Applicable</span>
                        <Badge variant={statutory.isPtApplicable ? 'default' : 'secondary'}>
                          {statutory.isPtApplicable ? 'Yes' : 'No'}
                        </Badge>
                      </div>
                      {statutory.ptState && (
                        <div className="flex justify-between">
                          <span className="text-slate-500">PT State</span>
                          <span className="font-medium">{statutory.ptState}</span>
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
                          <Badge variant="outline">{event.eventType}</Badge>
                        </TableCell>
                        <TableCell><DateDisplay date={event.eventDate} /></TableCell>
                        <TableCell><DateDisplay date={event.effectiveDate} /></TableCell>
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

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  GraduationCap,
  Calendar,
  Clock,
  MapPin,
  User,
  CheckCircle,
  BookOpen,
  Award,
  ExternalLink,
} from 'lucide-react';

// Mock data - Upcoming trainings
const upcomingTrainings = [
  {
    id: '1',
    name: 'Advanced React Patterns',
    description: 'Learn advanced React patterns including hooks, context, and performance optimization',
    trainer: 'External - Tech Academy',
    type: 'ONLINE',
    startDate: '2025-01-25',
    endDate: '2025-01-26',
    timing: '10:00 AM - 4:00 PM',
    location: 'Zoom',
    status: 'NOMINATED',
    mandatory: false,
  },
  {
    id: '2',
    name: 'Compliance & Ethics Training',
    description: 'Annual mandatory compliance training covering POSH, anti-corruption, and code of conduct',
    trainer: 'Internal - HR Team',
    type: 'ONLINE',
    startDate: '2025-02-01',
    endDate: '2025-02-01',
    timing: '2:00 PM - 5:00 PM',
    location: 'MS Teams',
    status: 'CONFIRMED',
    mandatory: true,
  },
  {
    id: '3',
    name: 'Leadership Development Program',
    description: 'Developing leadership skills for high-potential employees',
    trainer: 'External - Leadership Institute',
    type: 'IN_PERSON',
    startDate: '2025-02-15',
    endDate: '2025-02-17',
    timing: '9:00 AM - 6:00 PM',
    location: 'Mumbai Office',
    status: 'WAITLISTED',
    mandatory: false,
  },
];

// Mock data - Completed trainings
const completedTrainings = [
  {
    id: '1',
    name: 'New Employee Orientation',
    completedDate: '2024-03-15',
    trainer: 'HR Team',
    duration: '8 hours',
    score: 92,
    certificate: true,
  },
  {
    id: '2',
    name: 'Git & Version Control',
    completedDate: '2024-04-20',
    trainer: 'Tech Lead - Amit',
    duration: '4 hours',
    score: 88,
    certificate: true,
  },
  {
    id: '3',
    name: 'Agile Methodology',
    completedDate: '2024-06-10',
    trainer: 'External - Agile Coach',
    duration: '16 hours',
    score: 95,
    certificate: true,
  },
  {
    id: '4',
    name: 'Information Security Awareness',
    completedDate: '2024-08-15',
    trainer: 'IT Security Team',
    duration: '2 hours',
    score: 100,
    certificate: false,
  },
  {
    id: '5',
    name: 'TypeScript Fundamentals',
    completedDate: '2024-10-05',
    trainer: 'Self-paced',
    duration: '12 hours',
    score: 90,
    certificate: true,
  },
];

// Mock data - Available for nomination
const availableTrainings = [
  {
    id: '1',
    name: 'AWS Solutions Architect',
    description: 'Prepare for AWS Solutions Architect certification',
    trainer: 'External - AWS Partner',
    type: 'ONLINE',
    startDate: '2025-03-01',
    duration: '40 hours',
    seats: 5,
    enrolled: 3,
  },
  {
    id: '2',
    name: 'Project Management Basics',
    description: 'Introduction to project management concepts and tools',
    trainer: 'Internal - PMO',
    type: 'IN_PERSON',
    startDate: '2025-03-15',
    duration: '16 hours',
    seats: 20,
    enrolled: 12,
  },
];

export default function ESSTrainingList() {
  const [activeTab, setActiveTab] = useState('upcoming');

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'NOMINATED':
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800">Nominated</Badge>;
      case 'CONFIRMED':
        return <Badge variant="default" className="bg-green-500">Confirmed</Badge>;
      case 'WAITLISTED':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Waitlisted</Badge>;
      case 'COMPLETED':
        return <Badge variant="default">Completed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getTypeBadge = (type: string) => {
    return type === 'ONLINE' ? (
      <Badge variant="outline">Online</Badge>
    ) : (
      <Badge variant="outline">In-Person</Badge>
    );
  };

  const totalHours = completedTrainings.reduce((sum, t) => sum + parseInt(t.duration), 0);
  const certificatesEarned = completedTrainings.filter(t => t.certificate).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Training"
        subtitle="View and manage your training programs"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <BookOpen className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{completedTrainings.length}</div>
                <div className="text-sm text-muted-foreground">Completed</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Clock className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalHours}</div>
                <div className="text-sm text-muted-foreground">Total Hours</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Award className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{certificatesEarned}</div>
                <div className="text-sm text-muted-foreground">Certificates</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-orange-100 rounded-lg">
                <Calendar className="h-6 w-6 text-orange-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{upcomingTrainings.length}</div>
                <div className="text-sm text-muted-foreground">Upcoming</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="upcoming">Upcoming Training</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
          <TabsTrigger value="available">Available Programs</TabsTrigger>
        </TabsList>

        <TabsContent value="upcoming" className="space-y-4">
          {upcomingTrainings.map((training) => (
            <Card key={training.id}>
              <CardContent className="pt-6">
                <div className="flex justify-between items-start">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-lg">{training.name}</h3>
                      {training.mandatory && (
                        <Badge variant="destructive" className="text-xs">Mandatory</Badge>
                      )}
                      {getStatusBadge(training.status)}
                      {getTypeBadge(training.type)}
                    </div>
                    <p className="text-sm text-muted-foreground">{training.description}</p>
                    <div className="flex flex-wrap gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        {training.startDate === training.endDate
                          ? training.startDate
                          : `${training.startDate} - ${training.endDate}`}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        {training.timing}
                      </div>
                      <div className="flex items-center gap-1">
                        <MapPin className="h-4 w-4 text-muted-foreground" />
                        {training.location}
                      </div>
                      <div className="flex items-center gap-1">
                        <User className="h-4 w-4 text-muted-foreground" />
                        {training.trainer}
                      </div>
                    </div>
                  </div>
                  {training.type === 'ONLINE' && training.status === 'CONFIRMED' && (
                    <Button variant="outline" size="sm">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Join
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="completed">
          <Card>
            <CardHeader>
              <CardTitle>Completed Training Programs</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Training Name</TableHead>
                    <TableHead>Completed Date</TableHead>
                    <TableHead>Trainer</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead className="text-center">Score</TableHead>
                    <TableHead className="text-center">Certificate</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {completedTrainings.map((training) => (
                    <TableRow key={training.id}>
                      <TableCell className="font-medium">{training.name}</TableCell>
                      <TableCell>{training.completedDate}</TableCell>
                      <TableCell>{training.trainer}</TableCell>
                      <TableCell>{training.duration}</TableCell>
                      <TableCell className="text-center">
                        <Badge variant={training.score >= 90 ? 'default' : 'secondary'}>
                          {training.score}%
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        {training.certificate ? (
                          <Button variant="ghost" size="sm">
                            <Award className="h-4 w-4 text-yellow-500" />
                          </Button>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="available" className="space-y-4">
          {availableTrainings.map((training) => (
            <Card key={training.id}>
              <CardContent className="pt-6">
                <div className="flex justify-between items-start">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-lg">{training.name}</h3>
                      {getTypeBadge(training.type)}
                    </div>
                    <p className="text-sm text-muted-foreground">{training.description}</p>
                    <div className="flex flex-wrap gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        Starts: {training.startDate}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        {training.duration}
                      </div>
                      <div className="flex items-center gap-1">
                        <User className="h-4 w-4 text-muted-foreground" />
                        {training.trainer}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={(training.enrolled / training.seats) * 100} className="w-32" />
                      <span className="text-sm text-muted-foreground">
                        {training.enrolled}/{training.seats} enrolled
                      </span>
                    </div>
                  </div>
                  <Button disabled={training.enrolled >= training.seats}>
                    Request Nomination
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}

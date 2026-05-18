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
import { useState } from 'react';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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

interface UpcomingTraining {
  id: string;
  name: string;
  description: string;
  trainer: string;
  type: string;
  startDate: string;
  endDate: string;
  timing: string;
  location: string;
  status: string;
  mandatory: boolean;
}

interface CompletedTraining {
  id: string;
  name: string;
  completedDate: string;
  trainer: string;
  duration: string;
  score: number;
  certificate: boolean;
}

interface AvailableTraining {
  id: string;
  name: string;
  description: string;
  trainer: string;
  type: string;
  startDate: string;
  duration: string;
  seats: number;
  enrolled: number;
}

const upcomingTrainings: UpcomingTraining[] = [];
const completedTrainings: CompletedTraining[] = [];
const availableTrainings: AvailableTraining[] = [];

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
          {upcomingTrainings.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-sm text-muted-foreground">
                Training nomination data is pending ESS training endpoints. Upcoming programs will appear after HRIS training APIs are exposed to ESS.
              </CardContent>
            </Card>
          ) : upcomingTrainings.map((training) => (
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
                  {completedTrainings.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="py-8 text-center text-sm text-muted-foreground">
                        No completed training data is available from ESS yet.
                      </TableCell>
                    </TableRow>
                  ) : completedTrainings.map((training) => (
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
          {availableTrainings.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-sm text-muted-foreground">
                Available program nomination data is pending ESS training endpoints.
              </CardContent>
            </Card>
          ) : availableTrainings.map((training) => (
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

/**
 * Customer Portal - Support Page
 * Service requests and support tickets
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  HelpCircle,
  MessageSquare,
  Plus,
  Loader2,
  Clock,
  CheckCircle,
  AlertCircle,
  ChevronRight,
  Send,
  FileText,
  Calendar,
  IndianRupee,
} from 'lucide-react';
import { portalServiceRequestApi, portalCommunicationApi, portalDashboardApi } from '@/services/portalApi';
import type { ServiceRequest, SupportTicket, LoanSummary } from '@/types/portal';

const requestTypeLabels: Record<string, { label: string; description: string; icon: any }> = {
  PREPAYMENT: {
    label: 'Prepayment Request',
    description: 'Request for part prepayment of your loan',
    icon: IndianRupee,
  },
  FORECLOSURE: {
    label: 'Foreclosure Request',
    description: 'Close your loan account before maturity',
    icon: CheckCircle,
  },
  EMI_DATE_CHANGE: {
    label: 'EMI Date Change',
    description: 'Change your monthly EMI deduction date',
    icon: Calendar,
  },
  ADDRESS_CHANGE: {
    label: 'Address Change',
    description: 'Update your communication address',
    icon: FileText,
  },
  NOC_REQUEST: {
    label: 'NOC Request',
    description: 'Request No Objection Certificate',
    icon: FileText,
  },
  STATEMENT_REQUEST: {
    label: 'Statement Request',
    description: 'Request physical copy of account statement',
    icon: FileText,
  },
  GENERAL_QUERY: {
    label: 'General Query',
    description: 'Any other queries or information needed',
    icon: HelpCircle,
  },
  COMPLAINT: {
    label: 'Register Complaint',
    description: 'File a complaint about services',
    icon: AlertCircle,
  },
};

const statusColors: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-700',
  IN_PROGRESS: 'bg-blue-100 text-blue-700',
  COMPLETED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-700',
  CANCELLED: 'bg-gray-100 text-gray-700',
  OPEN: 'bg-yellow-100 text-yellow-700',
  RESOLVED: 'bg-green-100 text-green-700',
  CLOSED: 'bg-gray-100 text-gray-700',
};

export default function PortalSupport() {
  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loans, setLoans] = useState<LoanSummary[]>([]);
  const [activeTab, setActiveTab] = useState('requests');
  const [showNewRequest, setShowNewRequest] = useState(false);
  const [showNewTicket, setShowNewTicket] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<ServiceRequest | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);

  // New request form
  const [requestType, setRequestType] = useState('');
  const [requestLoan, setRequestLoan] = useState('');
  const [requestSubject, setRequestSubject] = useState('');
  const [requestDescription, setRequestDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // New ticket form
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketCategory, setTicketCategory] = useState('');
  const [ticketDescription, setTicketDescription] = useState('');
  const [ticketLoan, setTicketLoan] = useState('');

  // Reply
  const [replyMessage, setReplyMessage] = useState('');
  const [sendingReply, setSendingReply] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [requestsRes, ticketsRes, loansRes] = await Promise.all([
        portalServiceRequestApi.getRequests(),
        portalCommunicationApi.getTickets(),
        portalDashboardApi.getLoans(),
      ]);
      setRequests(requestsRes.data);
      setTickets(ticketsRes.data);
      setLoans(loansRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRequest = async () => {
    if (!requestType || !requestSubject || !requestDescription) return;

    setSubmitting(true);
    try {
      await portalServiceRequestApi.createRequest({
        request_type: requestType,
        loan_account_id: requestLoan || undefined,
        subject: requestSubject,
        description: requestDescription,
      });
      setShowNewRequest(false);
      resetRequestForm();
      fetchData();
    } catch (error) {
      console.error('Failed to create request:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateTicket = async () => {
    if (!ticketSubject || !ticketCategory || !ticketDescription) return;

    setSubmitting(true);
    try {
      await portalCommunicationApi.createTicket({
        subject: ticketSubject,
        category: ticketCategory,
        description: ticketDescription,
        loan_account_id: ticketLoan || undefined,
      });
      setShowNewTicket(false);
      resetTicketForm();
      fetchData();
    } catch (error) {
      console.error('Failed to create ticket:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSendReply = async () => {
    if (!selectedTicket || !replyMessage.trim()) return;

    setSendingReply(true);
    try {
      await portalCommunicationApi.addTicketReply(selectedTicket.id, { message: replyMessage });
      setReplyMessage('');
      // Refresh ticket details
      const response = await portalCommunicationApi.getTicket(selectedTicket.id);
      setSelectedTicket(response.data);
    } catch (error) {
      console.error('Failed to send reply:', error);
    } finally {
      setSendingReply(false);
    }
  };

  const resetRequestForm = () => {
    setRequestType('');
    setRequestLoan('');
    setRequestSubject('');
    setRequestDescription('');
  };

  const resetTicketForm = () => {
    setTicketSubject('');
    setTicketCategory('');
    setTicketDescription('');
    setTicketLoan('');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Support"
        subtitle="Manage your service requests and support tickets"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="requests">
            Service Requests ({requests.length})
          </TabsTrigger>
          <TabsTrigger value="tickets">
            Support Tickets ({tickets.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="requests" className="space-y-6">
          {/* Quick Actions */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(requestTypeLabels).slice(0, 4).map(([type, info]) => (
              <Card
                key={type}
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => {
                  setRequestType(type);
                  setShowNewRequest(true);
                }}
              >
                <CardContent className="p-4 text-center">
                  <div className="p-3 bg-emerald-100 rounded-lg inline-flex mb-2">
                    <info.icon className="h-5 w-5 text-emerald-600" />
                  </div>
                  <p className="font-medium text-sm">{info.label}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Service Requests List */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">My Service Requests</CardTitle>
              <Button onClick={() => setShowNewRequest(true)}>
                <Plus className="h-4 w-4 mr-2" />
                New Request
              </Button>
            </CardHeader>
            <CardContent>
              {requests.length > 0 ? (
                <div className="divide-y">
                  {requests.map((request) => (
                    <div
                      key={request.id}
                      className="flex items-center justify-between py-4 cursor-pointer hover:bg-gray-50 -mx-4 px-4"
                      onClick={() => setSelectedRequest(request)}
                    >
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-gray-100 rounded-lg">
                          <FileText className="h-5 w-5 text-gray-600" />
                        </div>
                        <div>
                          <p className="font-medium">{request.subject}</p>
                          <p className="text-sm text-gray-500">
                            {request.request_number} •{' '}
                            {requestTypeLabels[request.request_type]?.label || request.request_type}
                          </p>
                          <p className="text-xs text-gray-400">
                            {new Date(request.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={statusColors[request.status]}>
                          {request.status.replace('_', ' ')}
                        </Badge>
                        <ChevronRight className="h-4 w-4 text-gray-400" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No service requests yet</p>
                  <Button variant="link" onClick={() => setShowNewRequest(true)}>
                    Create your first request
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tickets" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Support Tickets</CardTitle>
              <Button onClick={() => setShowNewTicket(true)}>
                <Plus className="h-4 w-4 mr-2" />
                New Ticket
              </Button>
            </CardHeader>
            <CardContent>
              {tickets.length > 0 ? (
                <div className="divide-y">
                  {tickets.map((ticket) => (
                    <div
                      key={ticket.id}
                      className="flex items-center justify-between py-4 cursor-pointer hover:bg-gray-50 -mx-4 px-4"
                      onClick={async () => {
                        const response = await portalCommunicationApi.getTicket(ticket.id);
                        setSelectedTicket(response.data);
                      }}
                    >
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-blue-100 rounded-lg">
                          <MessageSquare className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium">{ticket.subject}</p>
                          <p className="text-sm text-gray-500">
                            {ticket.ticket_number} • {ticket.category}
                          </p>
                          <p className="text-xs text-gray-400">
                            {new Date(ticket.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={statusColors[ticket.status]}>{ticket.status}</Badge>
                        <Badge
                          variant="outline"
                          className={
                            ticket.priority === 'HIGH'
                              ? 'border-red-500 text-red-500'
                              : ticket.priority === 'MEDIUM'
                              ? 'border-yellow-500 text-yellow-500'
                              : 'border-gray-500 text-gray-500'
                          }
                        >
                          {ticket.priority}
                        </Badge>
                        <ChevronRight className="h-4 w-4 text-gray-400" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No support tickets yet</p>
                  <Button variant="link" onClick={() => setShowNewTicket(true)}>
                    Create a ticket
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* New Service Request Dialog */}
      <Dialog open={showNewRequest} onOpenChange={setShowNewRequest}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>New Service Request</DialogTitle>
            <DialogDescription>
              Submit a request and we'll get back to you within 2-3 business days
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Request Type</Label>
              <Select value={requestType} onValueChange={setRequestType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select request type" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(requestTypeLabels).map(([type, info]) => (
                    <SelectItem key={type} value={type}>
                      {info.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Loan Account (Optional)</Label>
              <Select value={requestLoan} onValueChange={setRequestLoan}>
                <SelectTrigger>
                  <SelectValue placeholder="Select loan if applicable" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Not Applicable</SelectItem>
                  {loans.map((loan) => (
                    <SelectItem key={loan.id} value={loan.id}>
                      {loan.loan_account_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Subject</Label>
              <Input
                placeholder="Brief description of your request"
                value={requestSubject}
                onChange={(e) => setRequestSubject(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                placeholder="Provide detailed information about your request"
                value={requestDescription}
                onChange={(e) => setRequestDescription(e.target.value)}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewRequest(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateRequest}
              disabled={!requestType || !requestSubject || !requestDescription || submitting}
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                'Submit Request'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* New Support Ticket Dialog */}
      <Dialog open={showNewTicket} onOpenChange={setShowNewTicket}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>New Support Ticket</DialogTitle>
            <DialogDescription>
              Get help from our support team
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Category</Label>
              <Select value={ticketCategory} onValueChange={setTicketCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PAYMENT">Payment Related</SelectItem>
                  <SelectItem value="LOAN">Loan Related</SelectItem>
                  <SelectItem value="DOCUMENT">Document Related</SelectItem>
                  <SelectItem value="TECHNICAL">Technical Issue</SelectItem>
                  <SelectItem value="OTHER">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Related Loan (Optional)</Label>
              <Select value={ticketLoan} onValueChange={setTicketLoan}>
                <SelectTrigger>
                  <SelectValue placeholder="Select loan if applicable" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Not Applicable</SelectItem>
                  {loans.map((loan) => (
                    <SelectItem key={loan.id} value={loan.id}>
                      {loan.loan_account_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Subject</Label>
              <Input
                placeholder="Brief description of your issue"
                value={ticketSubject}
                onChange={(e) => setTicketSubject(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                placeholder="Describe your issue in detail"
                value={ticketDescription}
                onChange={(e) => setTicketDescription(e.target.value)}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewTicket(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateTicket}
              disabled={!ticketCategory || !ticketSubject || !ticketDescription || submitting}
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Ticket'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Service Request Detail Dialog */}
      <Dialog open={!!selectedRequest} onOpenChange={() => setSelectedRequest(null)}>
        <DialogContent className="max-w-lg">
          {selectedRequest && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <DialogTitle>{selectedRequest.subject}</DialogTitle>
                  <Badge className={statusColors[selectedRequest.status]}>
                    {selectedRequest.status.replace('_', ' ')}
                  </Badge>
                </div>
                <DialogDescription>
                  {selectedRequest.request_number} • Created on{' '}
                  {new Date(selectedRequest.created_at).toLocaleDateString()}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Request Type</p>
                    <p className="font-medium">
                      {requestTypeLabels[selectedRequest.request_type]?.label ||
                        selectedRequest.request_type}
                    </p>
                  </div>
                  {selectedRequest.loan_account_number && (
                    <div>
                      <p className="text-gray-500">Loan Account</p>
                      <p className="font-medium">{selectedRequest.loan_account_number}</p>
                    </div>
                  )}
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">Description</p>
                  <p className="text-sm bg-gray-50 p-3 rounded-lg">
                    {selectedRequest.description}
                  </p>
                </div>
                {selectedRequest.resolution && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Resolution</p>
                    <p className="text-sm bg-green-50 p-3 rounded-lg text-green-800">
                      {selectedRequest.resolution}
                    </p>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Created</p>
                    <p className="font-medium">
                      {new Date(selectedRequest.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Last Updated</p>
                    <p className="font-medium">
                      {new Date(selectedRequest.updated_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Support Ticket Detail Dialog */}
      <Dialog open={!!selectedTicket} onOpenChange={() => setSelectedTicket(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          {selectedTicket && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <DialogTitle>{selectedTicket.subject}</DialogTitle>
                  <div className="flex gap-2">
                    <Badge className={statusColors[selectedTicket.status]}>
                      {selectedTicket.status}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={
                        selectedTicket.priority === 'HIGH'
                          ? 'border-red-500 text-red-500'
                          : selectedTicket.priority === 'MEDIUM'
                          ? 'border-yellow-500 text-yellow-500'
                          : 'border-gray-500 text-gray-500'
                      }
                    >
                      {selectedTicket.priority}
                    </Badge>
                  </div>
                </div>
                <DialogDescription>
                  {selectedTicket.ticket_number} • {selectedTicket.category}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                {/* Messages */}
                <div className="space-y-3 max-h-[300px] overflow-y-auto">
                  {selectedTicket.messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`p-3 rounded-lg ${
                        msg.sender_type === 'CUSTOMER'
                          ? 'bg-emerald-50 ml-8'
                          : 'bg-gray-50 mr-8'
                      }`}
                    >
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span className="font-medium">
                          {msg.sender_type === 'CUSTOMER' ? 'You' : 'Support Agent'}
                        </span>
                        <span>{new Date(msg.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-sm">{msg.message}</p>
                    </div>
                  ))}
                </div>

                {/* Reply Input */}
                {selectedTicket.status !== 'CLOSED' && (
                  <div className="flex gap-2">
                    <Input
                      placeholder="Type your reply..."
                      value={replyMessage}
                      onChange={(e) => setReplyMessage(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendReply();
                        }
                      }}
                    />
                    <Button
                      onClick={handleSendReply}
                      disabled={!replyMessage.trim() || sendingReply}
                    >
                      {sendingReply ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

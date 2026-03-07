import React, { useState, useEffect } from 'react';
import { payrollAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../components/ui/dropdown-menu';
import { Plus, MoreHorizontal, Loader2, Calendar, CheckCircle, XCircle, Clock, Pencil } from 'lucide-react';
import { toast } from 'sonner';

const statusColors = {
  pending: 'bg-amber-100 text-amber-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
};

const LEAVE_TYPES = [
  { value: 'annual', label: 'Annual Leave' },
  { value: 'sick', label: 'Sick Leave' },
  { value: 'casual', label: 'Casual Leave' },
  { value: 'maternity', label: 'Maternity Leave' },
  { value: 'paternity', label: 'Paternity Leave' },
];

export const LeaveManagement = () => {
  const [activeTab, setActiveTab] = useState('requests');
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [leaveBalances, setLeaveBalances] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [requestDialogOpen, setRequestDialogOpen] = useState(false);
  const [editBalanceDialogOpen, setEditBalanceDialogOpen] = useState(false);
  const [selectedBalance, setSelectedBalance] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [requestForm, setRequestForm] = useState({
    employee_id: '',
    leave_type: 'annual',
    start_date: '',
    end_date: '',
    reason: '',
  });

  const [balanceForm, setBalanceForm] = useState({
    annual: 0,
    sick: 0,
    casual: 0,
    maternity: 0,
    paternity: 0,
  });

  const fetchData = async () => {
    try {
      const params = {};
      if (statusFilter && statusFilter !== 'all') params.status = statusFilter;

      const [requestsRes, balancesRes, employeesRes] = await Promise.all([
        payrollAPI.getLeaveRequests(params),
        payrollAPI.getLeaveBalances(),
        payrollAPI.getEmployees({ status: 'active' }),
      ]);
      setLeaveRequests(requestsRes.data);
      setLeaveBalances(balancesRes.data);
      setEmployees(employeesRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const handleCreateRequest = async () => {
    setSubmitting(true);
    try {
      const response = await payrollAPI.createLeaveRequest(requestForm);
      toast.success(`Leave request created (${response.data.days} days)`);
      setRequestDialogOpen(false);
      setRequestForm({
        employee_id: '',
        leave_type: 'annual',
        start_date: '',
        end_date: '',
        reason: '',
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create leave request');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async (request) => {
    try {
      await payrollAPI.approveLeave(request.id);
      toast.success('Leave request approved');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve');
    }
  };

  const handleReject = async (request) => {
    try {
      await payrollAPI.rejectLeave(request.id);
      toast.success('Leave request rejected');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reject');
    }
  };

  const handleEditBalance = (balance) => {
    setSelectedBalance(balance);
    setBalanceForm({
      annual: balance.annual || 0,
      sick: balance.sick || 0,
      casual: balance.casual || 0,
      maternity: balance.maternity || 0,
      paternity: balance.paternity || 0,
    });
    setEditBalanceDialogOpen(true);
  };

  const handleUpdateBalance = async () => {
    setSubmitting(true);
    try {
      await payrollAPI.updateLeaveBalance(selectedBalance.employee_id, balanceForm);
      toast.success('Leave balance updated');
      setEditBalanceDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error('Failed to update balance');
    } finally {
      setSubmitting(false);
    }
  };

  const pendingCount = leaveRequests.filter(r => r.status === 'pending').length;

  return (
    <div className="space-y-6" data-testid="leave-management-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Leave Management
          </h2>
          <p className="text-slate-500 mt-1">
            {pendingCount > 0 ? `${pendingCount} pending requests` : 'Manage employee leave'}
          </p>
        </div>
        <Button onClick={() => setRequestDialogOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="create-leave-btn">
          <Plus className="w-4 h-4" />
          New Leave Request
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Clock className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Pending</p>
                <p className="text-2xl font-bold">{leaveRequests.filter(r => r.status === 'pending').length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Approved</p>
                <p className="text-2xl font-bold">{leaveRequests.filter(r => r.status === 'approved').length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <XCircle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Rejected</p>
                <p className="text-2xl font-bold">{leaveRequests.filter(r => r.status === 'rejected').length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <Calendar className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Days</p>
                <p className="text-2xl font-bold">{leaveRequests.filter(r => r.status === 'approved').reduce((sum, r) => sum + r.days, 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="requests">Leave Requests</TabsTrigger>
          <TabsTrigger value="balances">Leave Balances</TabsTrigger>
        </TabsList>

        <TabsContent value="requests" className="mt-4">
          {/* Filters */}
          <Card className="mb-4">
            <CardContent className="p-4">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="All Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* Requests Table */}
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
                </div>
              ) : leaveRequests.length === 0 ? (
                <div className="text-center py-16">
                  <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">No leave requests</h3>
                  <p className="text-slate-500 mt-1">Create a leave request for employees.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="table-header">
                      <TableHead className="table-header-cell">Employee</TableHead>
                      <TableHead className="table-header-cell">Leave Type</TableHead>
                      <TableHead className="table-header-cell">Period</TableHead>
                      <TableHead className="table-header-cell text-center">Days</TableHead>
                      <TableHead className="table-header-cell">Status</TableHead>
                      <TableHead className="table-header-cell w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leaveRequests.map((request) => (
                      <TableRow key={request.id} className="table-row" data-testid={`leave-row-${request.id}`}>
                        <TableCell className="table-cell">
                          <div>{request.employee_name}</div>
                          <span className="text-xs text-slate-400">{request.employee_code}</span>
                        </TableCell>
                        <TableCell className="table-cell capitalize">{request.leave_type}</TableCell>
                        <TableCell className="table-cell text-slate-500">
                          {request.start_date} to {request.end_date}
                        </TableCell>
                        <TableCell className="table-cell text-center font-medium">{request.days}</TableCell>
                        <TableCell className="table-cell">
                          <Badge className={statusColors[request.status]}>{request.status}</Badge>
                        </TableCell>
                        <TableCell className="table-cell">
                          {request.status === 'pending' && (
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreHorizontal className="w-4 h-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleApprove(request)}>
                                  <CheckCircle className="w-4 h-4 mr-2 text-green-600" />
                                  Approve
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleReject(request)}>
                                  <XCircle className="w-4 h-4 mr-2 text-red-600" />
                                  Reject
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
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

        <TabsContent value="balances" className="mt-4">
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
                </div>
              ) : leaveBalances.length === 0 ? (
                <div className="text-center py-16">
                  <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">No leave balances</h3>
                  <p className="text-slate-500 mt-1">Add employees to see leave balances.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="table-header">
                      <TableHead className="table-header-cell">Employee</TableHead>
                      <TableHead className="table-header-cell text-center">Annual</TableHead>
                      <TableHead className="table-header-cell text-center">Sick</TableHead>
                      <TableHead className="table-header-cell text-center">Casual</TableHead>
                      <TableHead className="table-header-cell text-center">Maternity</TableHead>
                      <TableHead className="table-header-cell text-center">Paternity</TableHead>
                      <TableHead className="table-header-cell w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leaveBalances.map((balance) => (
                      <TableRow key={balance.id} className="table-row">
                        <TableCell className="table-cell">
                          <div>{balance.employee_name}</div>
                          <span className="text-xs text-slate-400">{balance.employee_code}</span>
                        </TableCell>
                        <TableCell className="table-cell text-center">
                          <span className={balance.annual > 0 ? 'text-green-600 font-medium' : 'text-slate-400'}>
                            {balance.annual || 0}
                          </span>
                        </TableCell>
                        <TableCell className="table-cell text-center">
                          <span className={balance.sick > 0 ? 'text-green-600 font-medium' : 'text-slate-400'}>
                            {balance.sick || 0}
                          </span>
                        </TableCell>
                        <TableCell className="table-cell text-center">
                          <span className={balance.casual > 0 ? 'text-green-600 font-medium' : 'text-slate-400'}>
                            {balance.casual || 0}
                          </span>
                        </TableCell>
                        <TableCell className="table-cell text-center">
                          <span className={balance.maternity > 0 ? 'text-green-600 font-medium' : 'text-slate-400'}>
                            {balance.maternity || 0}
                          </span>
                        </TableCell>
                        <TableCell className="table-cell text-center">
                          <span className={balance.paternity > 0 ? 'text-green-600 font-medium' : 'text-slate-400'}>
                            {balance.paternity || 0}
                          </span>
                        </TableCell>
                        <TableCell className="table-cell">
                          <Button variant="ghost" size="icon" onClick={() => handleEditBalance(balance)}>
                            <Pencil className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Leave Request Dialog */}
      <Dialog open={requestDialogOpen} onOpenChange={setRequestDialogOpen}>
        <DialogContent data-testid="leave-request-dialog">
          <DialogHeader>
            <DialogTitle>New Leave Request</DialogTitle>
            <DialogDescription>Create a leave request for an employee</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Employee *</Label>
              <Select 
                value={requestForm.employee_id} 
                onValueChange={(v) => setRequestForm({ ...requestForm, employee_id: v })}
              >
                <SelectTrigger data-testid="leave-employee-select">
                  <SelectValue placeholder="Select employee" />
                </SelectTrigger>
                <SelectContent>
                  {employees.map((emp) => (
                    <SelectItem key={emp.id} value={emp.id}>
                      {emp.employee_id} - {emp.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Leave Type *</Label>
              <Select 
                value={requestForm.leave_type} 
                onValueChange={(v) => setRequestForm({ ...requestForm, leave_type: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LEAVE_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Start Date *</Label>
                <Input
                  type="date"
                  value={requestForm.start_date}
                  onChange={(e) => setRequestForm({ ...requestForm, start_date: e.target.value })}
                  data-testid="leave-start-date"
                />
              </div>
              <div className="space-y-2">
                <Label>End Date *</Label>
                <Input
                  type="date"
                  value={requestForm.end_date}
                  onChange={(e) => setRequestForm({ ...requestForm, end_date: e.target.value })}
                  data-testid="leave-end-date"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Reason</Label>
              <Textarea
                value={requestForm.reason}
                onChange={(e) => setRequestForm({ ...requestForm, reason: e.target.value })}
                placeholder="Optional reason for leave..."
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRequestDialogOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleCreateRequest} 
              disabled={submitting || !requestForm.employee_id || !requestForm.start_date || !requestForm.end_date} 
              className="bg-indigo-600 hover:bg-indigo-700"
              data-testid="submit-leave-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Create Request
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Balance Dialog */}
      <Dialog open={editBalanceDialogOpen} onOpenChange={setEditBalanceDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Leave Balance</DialogTitle>
            <DialogDescription>{selectedBalance?.employee_name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Annual Leave</Label>
                <Input
                  type="number"
                  value={balanceForm.annual}
                  onChange={(e) => setBalanceForm({ ...balanceForm, annual: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label>Sick Leave</Label>
                <Input
                  type="number"
                  value={balanceForm.sick}
                  onChange={(e) => setBalanceForm({ ...balanceForm, sick: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label>Casual Leave</Label>
                <Input
                  type="number"
                  value={balanceForm.casual}
                  onChange={(e) => setBalanceForm({ ...balanceForm, casual: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label>Maternity</Label>
                <Input
                  type="number"
                  value={balanceForm.maternity}
                  onChange={(e) => setBalanceForm({ ...balanceForm, maternity: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label>Paternity</Label>
                <Input
                  type="number"
                  value={balanceForm.paternity}
                  onChange={(e) => setBalanceForm({ ...balanceForm, paternity: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditBalanceDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdateBalance} disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Update Balance
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LeaveManagement;

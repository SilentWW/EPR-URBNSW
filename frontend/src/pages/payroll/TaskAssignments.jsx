import { useState, useEffect, useCallback } from 'react';
import { payrollAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Textarea } from '../../components/ui/textarea';
import { toast } from 'sonner';
import { Plus, ClipboardList, CheckCircle, Clock, XCircle, Play, Eye, Pencil, AlertCircle, BadgeCheck } from 'lucide-react';

const TaskAssignments = () => {
  const [tasks, setTasks] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [editMode, setEditMode] = useState(false);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [employeeFilter, setEmployeeFilter] = useState('all');
  
  // Form data
  const [formData, setFormData] = useState({
    employee_id: '',
    title: '',
    description: '',
    category: 'other',
    amount: '',
    due_date: '',
    notes: ''
  });

  const categories = [
    { value: 'design', label: 'Design', color: 'bg-purple-100 text-purple-800' },
    { value: 'development', label: 'Development', color: 'bg-blue-100 text-blue-800' },
    { value: 'marketing', label: 'Marketing', color: 'bg-green-100 text-green-800' },
    { value: 'production', label: 'Production', color: 'bg-orange-100 text-orange-800' },
    { value: 'admin', label: 'Administrative', color: 'bg-gray-100 text-gray-800' },
    { value: 'other', label: 'Other', color: 'bg-slate-100 text-slate-800' }
  ];

  const statuses = [
    { value: 'assigned', label: 'Assigned', color: 'bg-blue-100 text-blue-800', icon: ClipboardList },
    { value: 'in_progress', label: 'In Progress', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
    { value: 'completed', label: 'Completed', color: 'bg-orange-100 text-orange-800', icon: AlertCircle },
    { value: 'verified', label: 'Verified', color: 'bg-green-100 text-green-800', icon: CheckCircle },
    { value: 'cancelled', label: 'Cancelled', color: 'bg-red-100 text-red-800', icon: XCircle }
  ];

  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      const params = { include_paid: true };
      if (statusFilter !== 'all') params.status = statusFilter;
      if (categoryFilter !== 'all') params.category = categoryFilter;
      if (employeeFilter !== 'all') params.employee_id = employeeFilter;
      
      const res = await payrollAPI.getTasks(params);
      setTasks(res.data);
    } catch (err) {
      toast.error('Failed to load tasks');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, categoryFilter, employeeFilter]);

  const fetchEmployees = useCallback(async () => {
    try {
      const res = await payrollAPI.getEmployees({ status: 'active' });
      setEmployees(res.data);
    } catch (err) {
      console.error('Failed to load employees');
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    fetchEmployees();
  }, [fetchTasks, fetchEmployees]);

  const resetForm = () => {
    setFormData({
      employee_id: '',
      title: '',
      description: '',
      category: 'other',
      amount: '',
      due_date: '',
      notes: ''
    });
    setEditMode(false);
    setSelectedTask(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.employee_id || !formData.title || !formData.amount) {
      toast.error('Please fill in required fields');
      return;
    }

    try {
      const payload = {
        ...formData,
        amount: parseFloat(formData.amount)
      };

      if (editMode && selectedTask) {
        await payrollAPI.updateTask(selectedTask.id, payload);
        toast.success('Task updated successfully');
      } else {
        await payrollAPI.createTask(payload);
        toast.success('Task assigned successfully');
      }
      
      setShowDialog(false);
      resetForm();
      fetchTasks();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save task');
    }
  };

  const handleStartTask = async (taskId) => {
    try {
      await payrollAPI.startTask(taskId);
      toast.success('Task started');
      fetchTasks();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start task');
    }
  };

  const handleCompleteTask = async (taskId) => {
    try {
      await payrollAPI.completeTask(taskId);
      toast.success('Task marked as completed');
      fetchTasks();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to complete task');
    }
  };

  const handleVerifyTask = async (taskId) => {
    try {
      await payrollAPI.verifyTask(taskId);
      toast.success('Task verified - will be included in next payroll');
      fetchTasks();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to verify task');
    }
  };

  const handleRejectTask = async (taskId) => {
    const reason = prompt('Enter rejection reason (optional):');
    try {
      await payrollAPI.rejectTask(taskId, reason || '');
      toast.success('Task rejected and sent back for revision');
      fetchTasks();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reject task');
    }
  };

  const handleCancelTask = async (taskId) => {
    if (!confirm('Are you sure you want to cancel this task?')) return;
    
    const reason = prompt('Enter cancellation reason (optional):');
    try {
      await payrollAPI.cancelTask(taskId, reason || '');
      toast.success('Task cancelled');
      fetchTasks();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to cancel task');
    }
  };

  const openEditDialog = (task) => {
    setFormData({
      employee_id: task.employee_id,
      title: task.title,
      description: task.description || '',
      category: task.category,
      amount: task.amount.toString(),
      due_date: task.due_date || '',
      notes: task.notes || ''
    });
    setSelectedTask(task);
    setEditMode(true);
    setShowDialog(true);
  };

  const openDetailDialog = (task) => {
    setSelectedTask(task);
    setShowDetailDialog(true);
  };

  const getStatusBadge = (status) => {
    const s = statuses.find(st => st.value === status);
    if (!s) return null;
    const Icon = s.icon;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${s.color}`}>
        <Icon className="h-3 w-3" />
        {s.label}
      </span>
    );
  };

  const getCategoryBadge = (category) => {
    const c = categories.find(cat => cat.value === category);
    if (!c) return category;
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${c.color}`}>
        {c.label}
      </span>
    );
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-LK', { style: 'currency', currency: 'LKR' }).format(amount || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-LK');
  };

  // Stats
  const stats = {
    total: tasks.length,
    assigned: tasks.filter(t => t.status === 'assigned').length,
    inProgress: tasks.filter(t => t.status === 'in_progress').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    verified: tasks.filter(t => t.status === 'verified' && !t.payroll_id).length,
    pendingAmount: tasks.filter(t => t.status === 'verified' && !t.payroll_id).reduce((sum, t) => sum + (t.amount || 0), 0)
  };

  return (
    <div className="space-y-6" data-testid="task-assignments-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Task Assignments</h1>
          <p className="text-gray-600">Assign and track task-based payments for employees</p>
        </div>
        <Button onClick={() => { resetForm(); setShowDialog(true); }} data-testid="assign-task-btn">
          <Plus className="h-4 w-4 mr-2" />
          Assign Task
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-xs text-gray-500">Total Tasks</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-blue-600">{stats.assigned}</div>
            <div className="text-xs text-gray-500">Assigned</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-yellow-600">{stats.inProgress}</div>
            <div className="text-xs text-gray-500">In Progress</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-orange-600">{stats.completed}</div>
            <div className="text-xs text-gray-500">Awaiting Verification</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-green-600">{stats.verified}</div>
            <div className="text-xs text-gray-500">Verified (Unpaid)</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-purple-600">{formatCurrency(stats.pendingAmount)}</div>
            <div className="text-xs text-gray-500">Pending Payment</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40" data-testid="status-filter">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            {statuses.map(s => (
              <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-40" data-testid="category-filter">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map(c => (
              <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={employeeFilter} onValueChange={setEmployeeFilter}>
          <SelectTrigger className="w-52" data-testid="employee-filter">
            <SelectValue placeholder="Employee" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Employees</SelectItem>
            {employees.map(e => (
              <SelectItem key={e.id} value={e.id}>
                {e.employee_id} - {e.first_name} {e.last_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Tasks List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading tasks...</div>
          ) : tasks.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <ClipboardList className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>No tasks found</p>
              <Button variant="outline" className="mt-4" onClick={() => { resetForm(); setShowDialog(true); }}>
                Assign First Task
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Task</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Employee</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Category</th>
                    <th className="text-right px-4 py-3 text-sm font-medium text-gray-600">Amount</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Due Date</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Status</th>
                    <th className="text-right px-4 py-3 text-sm font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {tasks.map(task => (
                    <tr key={task.id} className="hover:bg-gray-50" data-testid={`task-row-${task.id}`}>
                      <td className="px-4 py-3">
                        <div>
                          <div className="font-medium text-gray-900">{task.title}</div>
                          <div className="text-xs text-gray-500">{task.task_number}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-900">{task.employee_name}</div>
                        <div className="text-xs text-gray-500">{task.employee_code}</div>
                      </td>
                      <td className="px-4 py-3">{getCategoryBadge(task.category)}</td>
                      <td className="px-4 py-3 text-right font-medium">{formatCurrency(task.amount)}</td>
                      <td className="px-4 py-3 text-sm">{formatDate(task.due_date)}</td>
                      <td className="px-4 py-3">
                        {getStatusBadge(task.status)}
                        {task.payroll_id && (
                          <span className="ml-2 text-xs text-green-600 flex items-center gap-1">
                            <BadgeCheck className="h-3 w-3" /> Paid
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" onClick={() => openDetailDialog(task)} data-testid={`view-task-${task.id}`}>
                            <Eye className="h-4 w-4" />
                          </Button>
                          
                          {/* Action buttons based on status */}
                          {task.status === 'assigned' && (
                            <>
                              <Button variant="ghost" size="sm" onClick={() => handleStartTask(task.id)} title="Start Task" data-testid={`start-task-${task.id}`}>
                                <Play className="h-4 w-4 text-blue-600" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => openEditDialog(task)} data-testid={`edit-task-${task.id}`}>
                                <Pencil className="h-4 w-4" />
                              </Button>
                            </>
                          )}
                          
                          {task.status === 'in_progress' && (
                            <Button variant="ghost" size="sm" onClick={() => handleCompleteTask(task.id)} title="Mark Complete" data-testid={`complete-task-${task.id}`}>
                              <CheckCircle className="h-4 w-4 text-orange-600" />
                            </Button>
                          )}
                          
                          {task.status === 'completed' && (
                            <>
                              <Button variant="ghost" size="sm" onClick={() => handleVerifyTask(task.id)} title="Verify" data-testid={`verify-task-${task.id}`}>
                                <BadgeCheck className="h-4 w-4 text-green-600" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleRejectTask(task.id)} title="Reject" data-testid={`reject-task-${task.id}`}>
                                <XCircle className="h-4 w-4 text-red-600" />
                              </Button>
                            </>
                          )}
                          
                          {!task.payroll_id && task.status !== 'cancelled' && (
                            <Button variant="ghost" size="sm" onClick={() => handleCancelTask(task.id)} title="Cancel" data-testid={`cancel-task-${task.id}`}>
                              <XCircle className="h-4 w-4 text-gray-400" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={(open) => { setShowDialog(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editMode ? 'Edit Task' : 'Assign New Task'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>Employee *</Label>
              <Select value={formData.employee_id} onValueChange={(v) => setFormData(prev => ({ ...prev, employee_id: v }))}>
                <SelectTrigger data-testid="task-employee-select">
                  <SelectValue placeholder="Select employee" />
                </SelectTrigger>
                <SelectContent>
                  {employees.map(e => (
                    <SelectItem key={e.id} value={e.id}>
                      {e.employee_id} - {e.first_name} {e.last_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Task Title *</Label>
              <Input
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="e.g., Design artwork for new collection"
                data-testid="task-title-input"
              />
            </div>

            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Task details and requirements"
                rows={3}
                data-testid="task-description-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Category *</Label>
                <Select value={formData.category} onValueChange={(v) => setFormData(prev => ({ ...prev, category: v }))}>
                  <SelectTrigger data-testid="task-category-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map(c => (
                      <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Payment Amount (LKR) *</Label>
                <Input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData(prev => ({ ...prev, amount: e.target.value }))}
                  placeholder="5000"
                  min="0"
                  step="0.01"
                  data-testid="task-amount-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Due Date</Label>
              <Input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                data-testid="task-due-date-input"
              />
            </div>

            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={formData.notes}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Additional notes"
                rows={2}
                data-testid="task-notes-input"
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>
                Cancel
              </Button>
              <Button type="submit" data-testid="save-task-btn">
                {editMode ? 'Update Task' : 'Assign Task'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Task Details</DialogTitle>
          </DialogHeader>
          {selectedTask && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">{selectedTask.task_number}</span>
                {getStatusBadge(selectedTask.status)}
              </div>
              
              <div>
                <h3 className="font-semibold text-lg">{selectedTask.title}</h3>
                {selectedTask.description && (
                  <p className="text-gray-600 mt-1">{selectedTask.description}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Employee:</span>
                  <p className="font-medium">{selectedTask.employee_name}</p>
                  <p className="text-xs text-gray-500">{selectedTask.employee_code}</p>
                </div>
                <div>
                  <span className="text-gray-500">Category:</span>
                  <p>{getCategoryBadge(selectedTask.category)}</p>
                </div>
                <div>
                  <span className="text-gray-500">Payment Amount:</span>
                  <p className="font-bold text-green-600">{formatCurrency(selectedTask.amount)}</p>
                </div>
                <div>
                  <span className="text-gray-500">Due Date:</span>
                  <p className="font-medium">{formatDate(selectedTask.due_date)}</p>
                </div>
              </div>

              <div className="border-t pt-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Assigned:</span>
                  <span>{formatDate(selectedTask.assigned_at)}</span>
                </div>
                {selectedTask.started_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Started:</span>
                    <span>{formatDate(selectedTask.started_at)}</span>
                  </div>
                )}
                {selectedTask.completed_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Completed:</span>
                    <span>{formatDate(selectedTask.completed_at)}</span>
                  </div>
                )}
                {selectedTask.verified_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Verified:</span>
                    <span>{formatDate(selectedTask.verified_at)}</span>
                  </div>
                )}
                {selectedTask.payroll_id && (
                  <div className="flex justify-between text-green-600">
                    <span>Paid in Payroll:</span>
                    <span className="font-medium">Yes</span>
                  </div>
                )}
              </div>

              {selectedTask.notes && (
                <div className="border-t pt-4">
                  <span className="text-sm text-gray-500">Notes:</span>
                  <p className="text-sm">{selectedTask.notes}</p>
                </div>
              )}

              {selectedTask.rejection_reason && (
                <div className="bg-red-50 p-3 rounded-md">
                  <span className="text-sm text-red-600 font-medium">Rejection Reason:</span>
                  <p className="text-sm text-red-800">{selectedTask.rejection_reason}</p>
                </div>
              )}

              {selectedTask.cancellation_reason && (
                <div className="bg-gray-50 p-3 rounded-md">
                  <span className="text-sm text-gray-600 font-medium">Cancellation Reason:</span>
                  <p className="text-sm text-gray-800">{selectedTask.cancellation_reason}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TaskAssignments;

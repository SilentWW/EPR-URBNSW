import { useState, useEffect, useCallback } from 'react';
import { payrollAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Textarea } from '../../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { toast } from 'sonner';
import { 
  Calendar, Clock, Users, CheckCircle, XCircle, AlertTriangle, 
  ChevronLeft, ChevronRight, Save, FileText, Coffee
} from 'lucide-react';

const AttendanceTracking = () => {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [dailyRecords, setDailyRecords] = useState([]);
  const [monthlyReport, setMonthlyReport] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [activeTab, setActiveTab] = useState('daily');
  
  // Attendance settings
  const FULL_DAY_HOURS = 9;
  const HALF_DAY_HOURS = 5;

  const statuses = [
    { value: 'present', label: 'Present', color: 'bg-green-100 text-green-800', icon: CheckCircle },
    { value: 'absent', label: 'Absent', color: 'bg-red-100 text-red-800', icon: XCircle },
    { value: 'half_day', label: 'Half Day', color: 'bg-yellow-100 text-yellow-800', icon: Coffee },
    { value: 'late', label: 'Late', color: 'bg-orange-100 text-orange-800', icon: AlertTriangle },
    { value: 'on_leave', label: 'On Leave', color: 'bg-blue-100 text-blue-800', icon: Calendar }
  ];

  const fetchDailyAttendance = useCallback(async () => {
    try {
      setLoading(true);
      const res = await payrollAPI.getDailyAttendance(selectedDate);
      setDailyRecords(res.data);
    } catch (err) {
      toast.error('Failed to load attendance');
    } finally {
      setLoading(false);
    }
  }, [selectedDate]);

  const fetchMonthlyReport = useCallback(async () => {
    try {
      setLoading(true);
      const params = { month: selectedMonth };
      if (departmentFilter !== 'all') params.department_id = departmentFilter;
      const res = await payrollAPI.getMonthlyAttendanceReport(params);
      setMonthlyReport(res.data);
    } catch (err) {
      toast.error('Failed to load monthly report');
    } finally {
      setLoading(false);
    }
  }, [selectedMonth, departmentFilter]);

  const fetchDepartments = useCallback(async () => {
    try {
      const res = await payrollAPI.getDepartments();
      setDepartments(res.data);
    } catch (err) {
      console.error('Failed to load departments');
    }
  }, []);

  useEffect(() => {
    fetchDepartments();
  }, [fetchDepartments]);

  useEffect(() => {
    if (activeTab === 'daily') {
      fetchDailyAttendance();
    } else {
      fetchMonthlyReport();
    }
  }, [activeTab, fetchDailyAttendance, fetchMonthlyReport]);

  const handleStatusChange = (employeeId, status) => {
    setDailyRecords(prev => prev.map(rec => {
      if (rec.employee_id === employeeId) {
        // Auto-set times based on status
        let check_in = rec.check_in;
        let check_out = rec.check_out;
        
        if (status === 'present' && !check_in) {
          check_in = '08:00';
          check_out = '17:00'; // 9 hours
        } else if (status === 'half_day' && !check_in) {
          check_in = '08:00';
          check_out = '13:00'; // 5 hours
        } else if (status === 'late' && !check_in) {
          check_in = '09:00';
          check_out = '17:00';
        } else if (status === 'absent' || status === 'on_leave') {
          check_in = null;
          check_out = null;
        }
        
        return { ...rec, status, check_in, check_out, modified: true };
      }
      return rec;
    }));
  };

  const handleTimeChange = (employeeId, field, value) => {
    setDailyRecords(prev => prev.map(rec => {
      if (rec.employee_id === employeeId) {
        return { ...rec, [field]: value, modified: true };
      }
      return rec;
    }));
  };

  const calculateHours = (checkIn, checkOut) => {
    if (!checkIn || !checkOut) return 0;
    try {
      const [inH, inM] = checkIn.split(':').map(Number);
      const [outH, outM] = checkOut.split(':').map(Number);
      const hours = (outH + outM/60) - (inH + inM/60);
      return Math.max(0, hours).toFixed(1);
    } catch {
      return 0;
    }
  };

  const saveAllAttendance = async () => {
    const modifiedRecords = dailyRecords.filter(r => r.modified && r.status);
    
    if (modifiedRecords.length === 0) {
      toast.info('No changes to save');
      return;
    }

    try {
      setSaving(true);
      
      const records = modifiedRecords.map(r => ({
        employee_id: r.employee_id,
        status: r.status,
        check_in: r.check_in,
        check_out: r.check_out,
        notes: r.notes
      }));

      await payrollAPI.createBulkAttendance({
        date: selectedDate,
        records
      });

      toast.success(`Saved attendance for ${records.length} employees`);
      fetchDailyAttendance();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save attendance');
    } finally {
      setSaving(false);
    }
  };

  const navigateDate = (direction) => {
    const date = new Date(selectedDate);
    date.setDate(date.getDate() + direction);
    setSelectedDate(date.toISOString().split('T')[0]);
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

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return `${days[date.getDay()]}, ${date.toLocaleDateString('en-LK', { day: 'numeric', month: 'long', year: 'numeric' })}`;
  };

  const isWeekend = (dateStr) => {
    const day = new Date(dateStr).getDay();
    return day === 0 || day === 6;
  };

  // Calculate daily stats
  const dailyStats = {
    total: dailyRecords.length,
    present: dailyRecords.filter(r => r.status === 'present').length,
    absent: dailyRecords.filter(r => r.status === 'absent').length,
    halfDay: dailyRecords.filter(r => r.status === 'half_day').length,
    late: dailyRecords.filter(r => r.status === 'late').length,
    onLeave: dailyRecords.filter(r => r.status === 'on_leave').length,
    notMarked: dailyRecords.filter(r => !r.status).length
  };

  return (
    <div className="space-y-6" data-testid="attendance-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Attendance Tracking</h1>
          <p className="text-gray-600">Track daily attendance and overtime (Full day: {FULL_DAY_HOURS}hrs, Half day: {HALF_DAY_HOURS}hrs)</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="daily" data-testid="daily-tab">
            <Calendar className="h-4 w-4 mr-2" />
            Daily Entry
          </TabsTrigger>
          <TabsTrigger value="monthly" data-testid="monthly-tab">
            <FileText className="h-4 w-4 mr-2" />
            Monthly Report
          </TabsTrigger>
        </TabsList>

        {/* Daily Entry Tab */}
        <TabsContent value="daily" className="space-y-4">
          {/* Date Navigation */}
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <Button variant="outline" onClick={() => navigateDate(-1)} data-testid="prev-date-btn">
                  <ChevronLeft className="h-4 w-4 mr-1" /> Previous
                </Button>
                
                <div className="flex items-center gap-4">
                  <Input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="w-40"
                    data-testid="date-picker"
                  />
                  <div className="text-center">
                    <p className="font-semibold">{formatDate(selectedDate)}</p>
                    {isWeekend(selectedDate) && (
                      <span className="text-xs text-orange-600 font-medium">Weekend (1.5x OT rate)</span>
                    )}
                  </div>
                </div>

                <Button variant="outline" onClick={() => navigateDate(1)} data-testid="next-date-btn">
                  Next <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-7 gap-3">
            <Card>
              <CardContent className="py-3 text-center">
                <div className="text-xl font-bold">{dailyStats.total}</div>
                <div className="text-xs text-gray-500">Total</div>
              </CardContent>
            </Card>
            <Card className="border-green-200 bg-green-50">
              <CardContent className="py-3 text-center">
                <div className="text-xl font-bold text-green-600">{dailyStats.present}</div>
                <div className="text-xs text-green-600">Present</div>
              </CardContent>
            </Card>
            <Card className="border-red-200 bg-red-50">
              <CardContent className="py-3 text-center">
                <div className="text-xl font-bold text-red-600">{dailyStats.absent}</div>
                <div className="text-xs text-red-600">Absent</div>
              </CardContent>
            </Card>
            <Card className="border-yellow-200 bg-yellow-50">
              <CardContent className="py-3 text-center">
                <div className="text-xl font-bold text-yellow-600">{dailyStats.halfDay}</div>
                <div className="text-xs text-yellow-600">Half Day</div>
              </CardContent>
            </Card>
            <Card className="border-orange-200 bg-orange-50">
              <CardContent className="py-3 text-center">
                <div className="text-xl font-bold text-orange-600">{dailyStats.late}</div>
                <div className="text-xs text-orange-600">Late</div>
              </CardContent>
            </Card>
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="py-3 text-center">
                <div className="text-xl font-bold text-blue-600">{dailyStats.onLeave}</div>
                <div className="text-xs text-blue-600">On Leave</div>
              </CardContent>
            </Card>
            <Card className="border-gray-200">
              <CardContent className="py-3 text-center">
                <div className="text-xl font-bold text-gray-500">{dailyStats.notMarked}</div>
                <div className="text-xs text-gray-500">Not Marked</div>
              </CardContent>
            </Card>
          </div>

          {/* Attendance Table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between py-3">
              <CardTitle className="text-lg">Employee Attendance</CardTitle>
              <Button 
                onClick={saveAllAttendance} 
                disabled={saving || !dailyRecords.some(r => r.modified)}
                data-testid="save-attendance-btn"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Saving...' : 'Save All'}
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? (
                <div className="p-8 text-center text-gray-500">Loading...</div>
              ) : dailyRecords.length === 0 ? (
                <div className="p-8 text-center text-gray-500">No employees found</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Employee</th>
                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Department</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">Status</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">Check In</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">Check Out</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">Hours</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">OT</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {dailyRecords.map(record => {
                        const hours = calculateHours(record.check_in, record.check_out);
                        const overtime = hours > 9 ? (hours - 9).toFixed(1) : 0;  // OT only for hours > 9
                        
                        return (
                          <tr 
                            key={record.employee_id} 
                            className={`hover:bg-gray-50 ${record.modified ? 'bg-yellow-50' : ''} ${record.is_on_approved_leave ? 'bg-blue-50' : ''}`}
                            data-testid={`attendance-row-${record.employee_id}`}
                          >
                            <td className="px-4 py-3">
                              <div className="font-medium">{record.employee_name}</div>
                              <div className="text-xs text-gray-500">{record.employee_code}</div>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">{record.department_name}</td>
                            <td className="px-4 py-3">
                              <Select
                                value={record.status || 'none'}
                                onValueChange={(v) => handleStatusChange(record.employee_id, v === 'none' ? null : v)}
                              >
                                <SelectTrigger className="w-32" data-testid={`status-select-${record.employee_id}`}>
                                  <SelectValue placeholder="Select" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="none">-- Select --</SelectItem>
                                  {statuses.map(s => (
                                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                              {record.is_on_approved_leave && !record.status && (
                                <span className="text-xs text-blue-600 block mt-1">Has approved leave</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-center">
                              <Input
                                type="time"
                                value={record.check_in || ''}
                                onChange={(e) => handleTimeChange(record.employee_id, 'check_in', e.target.value)}
                                className="w-24 text-center"
                                disabled={record.status === 'absent' || record.status === 'on_leave'}
                                data-testid={`checkin-${record.employee_id}`}
                              />
                            </td>
                            <td className="px-4 py-3 text-center">
                              <Input
                                type="time"
                                value={record.check_out || ''}
                                onChange={(e) => handleTimeChange(record.employee_id, 'check_out', e.target.value)}
                                className="w-24 text-center"
                                disabled={record.status === 'absent' || record.status === 'on_leave'}
                                data-testid={`checkout-${record.employee_id}`}
                              />
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span className={`font-medium ${hours >= 9 ? 'text-green-600' : hours >= 5 ? 'text-yellow-600' : 'text-gray-400'}`}>
                                {hours > 0 ? `${hours}h` : '-'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center">
                              {overtime > 0 && (
                                <span className="text-purple-600 font-medium">+{overtime}h</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Monthly Report Tab */}
        <TabsContent value="monthly" className="space-y-4">
          {/* Month Selector */}
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Label>Month:</Label>
                  <Input
                    type="month"
                    value={selectedMonth}
                    onChange={(e) => setSelectedMonth(e.target.value)}
                    className="w-40"
                    data-testid="month-picker"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Label>Department:</Label>
                  <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
                    <SelectTrigger className="w-48" data-testid="dept-filter">
                      <SelectValue placeholder="All Departments" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Departments</SelectItem>
                      {departments.map(d => (
                        <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Monthly Report Table */}
          <Card>
            <CardHeader>
              <CardTitle>Monthly Attendance Summary - {selectedMonth}</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? (
                <div className="p-8 text-center text-gray-500">Loading...</div>
              ) : monthlyReport.length === 0 ? (
                <div className="p-8 text-center text-gray-500">No data for this month</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Employee</th>
                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Department</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-green-600">Present</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-yellow-600">Half Day</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-red-600">Absent</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-orange-600">Late</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-blue-600">Leave</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">Work Days</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">Total Hrs</th>
                        <th className="text-center px-4 py-3 text-sm font-medium text-purple-600">OT Hrs</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {monthlyReport.map(emp => (
                        <tr key={emp.employee_id} className="hover:bg-gray-50" data-testid={`monthly-row-${emp.employee_id}`}>
                          <td className="px-4 py-3">
                            <div className="font-medium">{emp.employee_name}</div>
                            <div className="text-xs text-gray-500">{emp.employee_code}</div>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">{emp.department_name}</td>
                          <td className="px-4 py-3 text-center font-medium text-green-600">{emp.present_days}</td>
                          <td className="px-4 py-3 text-center font-medium text-yellow-600">{emp.half_days}</td>
                          <td className="px-4 py-3 text-center font-medium text-red-600">{emp.absent_days}</td>
                          <td className="px-4 py-3 text-center font-medium text-orange-600">{emp.late_days}</td>
                          <td className="px-4 py-3 text-center font-medium text-blue-600">{emp.leave_days}</td>
                          <td className="px-4 py-3 text-center font-bold">{emp.working_days}</td>
                          <td className="px-4 py-3 text-center">{emp.total_hours}h</td>
                          <td className="px-4 py-3 text-center font-medium text-purple-600">
                            {emp.total_overtime > 0 ? `${emp.total_overtime}h` : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-gray-100 border-t-2">
                      <tr>
                        <td colSpan={2} className="px-4 py-3 font-bold">Total</td>
                        <td className="px-4 py-3 text-center font-bold text-green-600">
                          {monthlyReport.reduce((sum, e) => sum + e.present_days, 0)}
                        </td>
                        <td className="px-4 py-3 text-center font-bold text-yellow-600">
                          {monthlyReport.reduce((sum, e) => sum + e.half_days, 0)}
                        </td>
                        <td className="px-4 py-3 text-center font-bold text-red-600">
                          {monthlyReport.reduce((sum, e) => sum + e.absent_days, 0)}
                        </td>
                        <td className="px-4 py-3 text-center font-bold text-orange-600">
                          {monthlyReport.reduce((sum, e) => sum + e.late_days, 0)}
                        </td>
                        <td className="px-4 py-3 text-center font-bold text-blue-600">
                          {monthlyReport.reduce((sum, e) => sum + e.leave_days, 0)}
                        </td>
                        <td className="px-4 py-3 text-center font-bold">
                          {monthlyReport.reduce((sum, e) => sum + e.working_days, 0)}
                        </td>
                        <td className="px-4 py-3 text-center font-bold">
                          {monthlyReport.reduce((sum, e) => sum + e.total_hours, 0).toFixed(1)}h
                        </td>
                        <td className="px-4 py-3 text-center font-bold text-purple-600">
                          {monthlyReport.reduce((sum, e) => sum + e.total_overtime, 0).toFixed(1)}h
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AttendanceTracking;

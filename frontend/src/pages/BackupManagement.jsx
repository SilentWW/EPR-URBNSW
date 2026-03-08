import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { toast } from 'sonner';
import { 
  Download, Upload, Trash2, RefreshCw, HardDrive, 
  Calendar, FileArchive, AlertTriangle, CheckCircle, Clock,
  Database, ArrowDownToLine, ArrowUpFromLine
} from 'lucide-react';

const BackupManagement = () => {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [confirmCode, setConfirmCode] = useState('');
  const [backupName, setBackupName] = useState('');
  const [backupDescription, setBackupDescription] = useState('');

  const fetchBackups = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/backups');
      setBackups(response.data);
    } catch (error) {
      toast.error('Failed to load backups');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBackups();
  }, [fetchBackups]);

  const createBackup = async () => {
    if (!backupName.trim()) {
      toast.error('Please enter a backup name');
      return;
    }

    try {
      setCreating(true);
      await api.post('/admin/backups', {
        name: backupName,
        description: backupDescription,
        backup_type: 'full'
      });
      toast.success('Backup created successfully');
      setShowCreateDialog(false);
      setBackupName('');
      setBackupDescription('');
      fetchBackups();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create backup');
    } finally {
      setCreating(false);
    }
  };

  const downloadBackup = async (backup) => {
    try {
      const response = await api.get(`/admin/backups/${backup.id}/download`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${backup.name}.json.gz`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Backup downloaded');
    } catch (error) {
      toast.error('Failed to download backup');
    }
  };

  const uploadBackup = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.json') && !file.name.endsWith('.json.gz') && !file.name.endsWith('.gz')) {
      toast.error('Invalid file type. Please upload a .json or .json.gz file');
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/admin/backups/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      toast.success(`Backup uploaded: ${response.data.total_records} records in ${response.data.collections.length} collections`);
      fetchBackups();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload backup');
    } finally {
      setUploading(false);
      event.target.value = ''; // Reset file input
    }
  };

  const deleteBackup = async (backup) => {
    if (!confirm(`Are you sure you want to delete backup "${backup.name}"?`)) return;

    try {
      await api.delete(`/admin/backups/${backup.id}`);
      toast.success('Backup deleted');
      fetchBackups();
    } catch (error) {
      toast.error('Failed to delete backup');
    }
  };

  const openRestoreDialog = (backup) => {
    setSelectedBackup(backup);
    setConfirmCode('');
    setShowRestoreDialog(true);
  };

  const restoreBackup = async () => {
    if (confirmCode !== 'RESTORE') {
      toast.error('Please type RESTORE to confirm');
      return;
    }

    try {
      await api.post('/admin/restore', {
        backup_id: selectedBackup.id,
        confirmation_code: 'RESTORE'
      });
      toast.success('Data restored successfully');
      setShowRestoreDialog(false);
      setSelectedBackup(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Restore failed');
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('en-LK', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      completed: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      in_progress: { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      failed: { color: 'bg-red-100 text-red-800', icon: AlertTriangle }
    };
    const config = statusConfig[status] || statusConfig.failed;
    const Icon = config.icon;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="h-3 w-3" />
        {status}
      </span>
    );
  };

  return (
    <div className="space-y-6" data-testid="backup-management-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Backup & Restore</h1>
          <p className="text-gray-500">Manage your data backups and restore points</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchBackups} data-testid="refresh-btn">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <label>
            <input
              type="file"
              accept=".json,.json.gz,.gz"
              onChange={uploadBackup}
              className="hidden"
              data-testid="upload-input"
            />
            <Button variant="outline" asChild disabled={uploading}>
              <span>
                <Upload className="h-4 w-4 mr-2" />
                {uploading ? 'Uploading...' : 'Upload Backup'}
              </span>
            </Button>
          </label>
          <Button onClick={() => setShowCreateDialog(true)} data-testid="create-backup-btn">
            <Download className="h-4 w-4 mr-2" />
            Create Backup
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Database className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{backups.length}</p>
                <p className="text-sm text-gray-500">Total Backups</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{backups.filter(b => b.status === 'completed').length}</p>
                <p className="text-sm text-gray-500">Completed</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <HardDrive className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {formatFileSize(backups.reduce((sum, b) => sum + (b.file_size || 0), 0))}
                </p>
                <p className="text-sm text-gray-500">Total Size</p>
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
                <p className="text-2xl font-bold">
                  {backups.length > 0 ? formatDate(backups[0]?.created_at).split(',')[0] : '-'}
                </p>
                <p className="text-sm text-gray-500">Latest Backup</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Backups List */}
      <Card>
        <CardHeader>
          <CardTitle>Backup History</CardTitle>
          <CardDescription>View and manage your backup files</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading backups...</div>
          ) : backups.length === 0 ? (
            <div className="text-center py-12">
              <FileArchive className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">No backups yet</h3>
              <p className="text-gray-500 mt-2">Create your first backup to protect your data</p>
              <Button className="mt-4" onClick={() => setShowCreateDialog(true)}>
                <Download className="h-4 w-4 mr-2" />
                Create First Backup
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Backup Name</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Created</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Size</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Records</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Status</th>
                    <th className="text-right px-4 py-3 text-sm font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {backups.map(backup => (
                    <tr key={backup.id} className="hover:bg-gray-50" data-testid={`backup-row-${backup.id}`}>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3">
                          <FileArchive className="h-5 w-5 text-gray-400" />
                          <div>
                            <div className="font-medium text-gray-900">{backup.name}</div>
                            {backup.description && (
                              <div className="text-xs text-gray-500">{backup.description}</div>
                            )}
                            {backup.is_uploaded && (
                              <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">Uploaded</span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-600">{formatDate(backup.created_at)}</td>
                      <td className="px-4 py-4 text-sm text-gray-600">{formatFileSize(backup.file_size)}</td>
                      <td className="px-4 py-4 text-sm text-gray-600">{backup.total_records?.toLocaleString() || '-'}</td>
                      <td className="px-4 py-4">{getStatusBadge(backup.status)}</td>
                      <td className="px-4 py-4">
                        <div className="flex justify-end gap-1">
                          {backup.status === 'completed' && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => downloadBackup(backup)}
                                title="Download"
                                data-testid={`download-${backup.id}`}
                              >
                                <ArrowDownToLine className="h-4 w-4 text-blue-600" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openRestoreDialog(backup)}
                                title="Restore"
                                data-testid={`restore-${backup.id}`}
                              >
                                <ArrowUpFromLine className="h-4 w-4 text-green-600" />
                              </Button>
                            </>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteBackup(backup)}
                            title="Delete"
                            data-testid={`delete-${backup.id}`}
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </Button>
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

      {/* Create Backup Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Backup</DialogTitle>
            <DialogDescription>
              Create a full backup of all your data. This may take a few moments.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="backup-name">Backup Name *</Label>
              <Input
                id="backup-name"
                value={backupName}
                onChange={(e) => setBackupName(e.target.value)}
                placeholder="e.g., Monthly Backup March 2026"
                data-testid="backup-name-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="backup-desc">Description (optional)</Label>
              <Input
                id="backup-desc"
                value={backupDescription}
                onChange={(e) => setBackupDescription(e.target.value)}
                placeholder="e.g., Before payroll processing"
                data-testid="backup-desc-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            <Button onClick={createBackup} disabled={creating}>
              {creating ? 'Creating...' : 'Create Backup'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Restore Dialog */}
      <Dialog open={showRestoreDialog} onOpenChange={setShowRestoreDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              Restore Backup
            </DialogTitle>
            <DialogDescription>
              This will replace your current data with data from the backup. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {selectedBackup && (
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="font-medium">{selectedBackup.name}</p>
                <p className="text-sm text-gray-500">Created: {formatDate(selectedBackup.created_at)}</p>
                <p className="text-sm text-gray-500">Records: {selectedBackup.total_records?.toLocaleString()}</p>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>Warning:</strong> A pre-restore backup will be created automatically before restoring.
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm-code">Type RESTORE to confirm</Label>
                <Input
                  id="confirm-code"
                  value={confirmCode}
                  onChange={(e) => setConfirmCode(e.target.value.toUpperCase())}
                  placeholder="RESTORE"
                  data-testid="confirm-restore-input"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRestoreDialog(false)}>Cancel</Button>
            <Button 
              variant="destructive" 
              onClick={restoreBackup}
              disabled={confirmCode !== 'RESTORE'}
            >
              Restore Data
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BackupManagement;

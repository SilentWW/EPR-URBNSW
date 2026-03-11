import { useState, useEffect } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Separator } from '../components/ui/separator';
import { toast } from 'sonner';
import {
  User,
  Phone,
  MapPin,
  Building2,
  Briefcase,
  Calendar,
  AlertCircle,
  Save,
  Loader2
} from 'lucide-react';

export default function MyProfile() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState(null);
  const [formData, setFormData] = useState({
    phone: '',
    address: '',
    city: '',
    state: '',
    postal_code: '',
    emergency_contact: {
      name: '',
      phone: '',
      relationship: ''
    }
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const res = await api.get('/portal/my-profile');
      setProfile(res.data);
      setFormData({
        phone: res.data.phone || '',
        address: res.data.address || '',
        city: res.data.city || '',
        state: res.data.state || '',
        postal_code: res.data.postal_code || '',
        emergency_contact: {
          name: res.data.emergency_contact?.name || '',
          phone: res.data.emergency_contact?.phone || '',
          relationship: res.data.emergency_contact?.relationship || ''
        }
      });
    } catch (error) {
      if (error.response?.status === 404) {
        setProfile(null);
      } else {
        toast.error('Failed to load profile');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await api.put('/portal/my-profile', formData);
      toast.success('Profile updated successfully');
      fetchProfile();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleEmergencyContactChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      emergency_contact: { ...prev.emergency_contact, [field]: value }
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="space-y-6" data-testid="my-profile-page">
        <div className="flex items-center gap-3">
          <User className="w-8 h-8 text-indigo-600" />
          <div>
            <h1 className="text-2xl font-bold text-slate-900">My Profile</h1>
            <p className="text-slate-500">Manage your personal information</p>
          </div>
        </div>

        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="py-6">
            <div className="flex items-center gap-3 text-amber-700">
              <AlertCircle className="w-6 h-6" />
              <div>
                <p className="font-medium">Employee Profile Not Found</p>
                <p className="text-sm mt-1">
                  Your user account is not linked to an employee record. Please contact your administrator.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="my-profile-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center">
            <User className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              {profile.first_name} {profile.last_name}
            </h1>
            <p className="text-slate-500">{profile.employee_id}</p>
          </div>
        </div>
        <Button onClick={handleSave} disabled={saving} data-testid="save-profile-btn">
          {saving ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Save Changes
        </Button>
      </div>

      {/* Employment Info (Read-only) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-slate-400" />
            Employment Information
          </CardTitle>
          <CardDescription>Contact your HR department to update these details</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <Label className="text-xs text-slate-500">Department</Label>
              <p className="font-medium">{profile.department_name || 'Not assigned'}</p>
            </div>
            <div>
              <Label className="text-xs text-slate-500">Designation</Label>
              <p className="font-medium">{profile.designation || 'Not specified'}</p>
            </div>
            <div>
              <Label className="text-xs text-slate-500">Hire Date</Label>
              <p className="font-medium flex items-center gap-1">
                <Calendar className="w-4 h-4 text-slate-400" />
                {(profile.hire_date || profile.join_date) ? new Date(profile.hire_date || profile.join_date).toLocaleDateString() : 'Not specified'}
              </p>
            </div>
            <div>
              <Label className="text-xs text-slate-500">Employment Type</Label>
              <p className="font-medium capitalize">{(profile.employment_type || profile.employee_type)?.replace('_', ' ') || 'Not specified'}</p>
            </div>
            <div>
              <Label className="text-xs text-slate-500">Email</Label>
              <p className="font-medium">{profile.email}</p>
            </div>
            <div>
              <Label className="text-xs text-slate-500">Status</Label>
              <p className="font-medium capitalize">{profile.status || 'Active'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contact Information (Editable) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Phone className="w-5 h-5 text-slate-400" />
            Contact Information
          </CardTitle>
          <CardDescription>Update your contact details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                placeholder="Enter phone number"
                data-testid="phone-input"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Address (Editable) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <MapPin className="w-5 h-5 text-slate-400" />
            Address
          </CardTitle>
          <CardDescription>Your residential address</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="address">Street Address</Label>
            <Input
              id="address"
              value={formData.address}
              onChange={(e) => handleChange('address', e.target.value)}
              placeholder="Enter street address"
              data-testid="address-input"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="city">City</Label>
              <Input
                id="city"
                value={formData.city}
                onChange={(e) => handleChange('city', e.target.value)}
                placeholder="City"
                data-testid="city-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="state">State/Province</Label>
              <Input
                id="state"
                value={formData.state}
                onChange={(e) => handleChange('state', e.target.value)}
                placeholder="State"
                data-testid="state-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="postal_code">Postal Code</Label>
              <Input
                id="postal_code"
                value={formData.postal_code}
                onChange={(e) => handleChange('postal_code', e.target.value)}
                placeholder="Postal code"
                data-testid="postal-code-input"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Emergency Contact (Editable) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-slate-400" />
            Emergency Contact
          </CardTitle>
          <CardDescription>Person to contact in case of emergency</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="ec_name">Contact Name</Label>
              <Input
                id="ec_name"
                value={formData.emergency_contact.name}
                onChange={(e) => handleEmergencyContactChange('name', e.target.value)}
                placeholder="Full name"
                data-testid="ec-name-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ec_phone">Contact Phone</Label>
              <Input
                id="ec_phone"
                value={formData.emergency_contact.phone}
                onChange={(e) => handleEmergencyContactChange('phone', e.target.value)}
                placeholder="Phone number"
                data-testid="ec-phone-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ec_relationship">Relationship</Label>
              <Input
                id="ec_relationship"
                value={formData.emergency_contact.relationship}
                onChange={(e) => handleEmergencyContactChange('relationship', e.target.value)}
                placeholder="e.g., Spouse, Parent, Sibling"
                data-testid="ec-relationship-input"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Cue, SlideElement } from '@/types/player';
import { Save, X, Play, Pause } from 'lucide-react';

interface CueEditorProps {
  cue: Cue;
  elements: SlideElement[];
  audioDuration: number;
  onSave: (cue: Cue) => void;
  onCancel: () => void;
  onPreview: (t0: number, t1: number) => void;
}

export const CueEditor: React.FC<CueEditorProps> = ({
  cue,
  elements,
  audioDuration,
  onSave,
  onCancel,
  onPreview
}) => {
  const [editedCue, setEditedCue] = useState<Cue>({ ...cue });
  const [isPreviewing, setIsPreviewing] = useState(false);

  const handleTimeChange = (field: 't0' | 't1', value: number) => {
    setEditedCue(prev => ({
      ...prev,
      [field]: Math.max(0, Math.min(audioDuration, value))
    }));
  };

  const handleBboxChange = (index: number, value: number) => {
    if (editedCue.bbox) {
      const newBbox = [...editedCue.bbox] as [number, number, number, number];
      newBbox[index] = value;
      setEditedCue(prev => ({ ...prev, bbox: newBbox }));
    }
  };

  const handleToChange = (index: number, value: number) => {
    if (editedCue.to) {
      const newTo = [...editedCue.to] as [number, number];
      newTo[index] = value;
      setEditedCue(prev => ({ ...prev, to: newTo }));
    }
  };

  const handlePreview = () => {
    if (isPreviewing) {
      setIsPreviewing(false);
    } else {
      setIsPreviewing(true);
      onPreview(editedCue.t0, editedCue.t1);
      // Auto-stop preview after duration
      setTimeout(() => setIsPreviewing(false), (editedCue.t1 - editedCue.t0) * 1000);
    }
  };

  const handleSave = () => {
    // Validate cue
    if (editedCue.t1 <= editedCue.t0) {
      alert('End time must be greater than start time');
      return;
    }

    if (editedCue.action === 'highlight' && (!editedCue.bbox || editedCue.bbox.length !== 4)) {
      alert('Highlight action requires valid bounding box');
      return;
    }

    if (editedCue.action === 'laser_move' && (!editedCue.to || editedCue.to.length !== 2)) {
      alert('Laser move action requires valid target position');
      return;
    }

    onSave(editedCue);
  };

  return (
    <Card className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Edit Cue</h3>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePreview}
            className="flex items-center space-x-1"
          >
            {isPreviewing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            <span>Preview</span>
          </Button>
          <Button variant="outline" size="sm" onClick={onCancel}>
            <X className="h-4 w-4" />
          </Button>
          <Button size="sm" onClick={handleSave}>
            <Save className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Timing */}
        <div className="space-y-2">
          <Label>Start Time (s)</Label>
          <Input
            type="number"
            value={editedCue.t0}
            onChange={(e) => handleTimeChange('t0', parseFloat(e.target.value) || 0)}
            step="0.1"
            min="0"
            max={audioDuration}
          />
        </div>

        <div className="space-y-2">
          <Label>End Time (s)</Label>
          <Input
            type="number"
            value={editedCue.t1}
            onChange={(e) => handleTimeChange('t1', parseFloat(e.target.value) || 0)}
            step="0.1"
            min="0"
            max={audioDuration}
          />
        </div>
      </div>

      {/* Duration Slider */}
      <div className="space-y-2">
        <Label>Duration: {(editedCue.t1 - editedCue.t0).toFixed(1)}s</Label>
        <Slider
          value={[editedCue.t0, editedCue.t1]}
          max={audioDuration}
          step={0.1}
          onValueChange={([start, end]) => {
            setEditedCue(prev => ({
              ...prev,
              t0: start,
              t1: end
            }));
          }}
          className="w-full"
        />
      </div>

      {/* Action Type */}
      <div className="space-y-2">
        <Label>Action Type</Label>
        <Select
          value={editedCue.action}
          onValueChange={(value: 'highlight' | 'underline' | 'laser_move') =>
            setEditedCue(prev => ({ ...prev, action: value }))
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="highlight">Highlight</SelectItem>
            <SelectItem value="underline">Underline</SelectItem>
            <SelectItem value="laser_move">Laser Move</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Element Selection */}
      <div className="space-y-2">
        <Label>Element</Label>
        <Select
          value={editedCue.element_id || ''}
          onValueChange={(value) =>
            setEditedCue(prev => ({ ...prev, element_id: value }))
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Select element" />
          </SelectTrigger>
          <SelectContent>
            {elements.map((element) => (
              <SelectItem key={element.id} value={element.id}>
                {element.text || element.id}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Bounding Box (for highlight/underline) */}
      {(editedCue.action === 'highlight' || editedCue.action === 'underline') && (
        <div className="space-y-2">
          <Label>Bounding Box</Label>
          <div className="grid grid-cols-4 gap-2">
            <div>
              <Label className="text-xs">X</Label>
              <Input
                type="number"
                value={editedCue.bbox?.[0] || 0}
                onChange={(e) => handleBboxChange(0, parseInt(e.target.value) || 0)}
              />
            </div>
            <div>
              <Label className="text-xs">Y</Label>
              <Input
                type="number"
                value={editedCue.bbox?.[1] || 0}
                onChange={(e) => handleBboxChange(1, parseInt(e.target.value) || 0)}
              />
            </div>
            <div>
              <Label className="text-xs">Width</Label>
              <Input
                type="number"
                value={editedCue.bbox?.[2] || 0}
                onChange={(e) => handleBboxChange(2, parseInt(e.target.value) || 0)}
              />
            </div>
            <div>
              <Label className="text-xs">Height</Label>
              <Input
                type="number"
                value={editedCue.bbox?.[3] || 0}
                onChange={(e) => handleBboxChange(3, parseInt(e.target.value) || 0)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Target Position (for laser_move) */}
      {editedCue.action === 'laser_move' && (
        <div className="space-y-2">
          <Label>Target Position</Label>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label className="text-xs">X</Label>
              <Input
                type="number"
                value={editedCue.to?.[0] || 0}
                onChange={(e) => handleToChange(0, parseInt(e.target.value) || 0)}
              />
            </div>
            <div>
              <Label className="text-xs">Y</Label>
              <Input
                type="number"
                value={editedCue.to?.[1] || 0}
                onChange={(e) => handleToChange(1, parseInt(e.target.value) || 0)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Validation Messages */}
      {editedCue.t1 <= editedCue.t0 && (
        <div className="text-sm text-red-500">
          End time must be greater than start time
        </div>
      )}
      
      {(editedCue.t1 - editedCue.t0) < 0.8 && (
        <div className="text-sm text-yellow-500">
          Duration is less than recommended minimum (0.8s)
        </div>
      )}
    </Card>
  );
};
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { SlideElement } from '@/types/player';
import { Save, X } from 'lucide-react';

interface ElementEditorProps {
  element: SlideElement;
  onSave: (element: SlideElement) => void;
  onCancel: () => void;
}

export const ElementEditor: React.FC<ElementEditorProps> = ({
  element,
  onSave,
  onCancel
}) => {
  const [editedElement, setEditedElement] = useState<SlideElement>({ ...element });

  const handleBboxChange = (index: number, value: number) => {
    const newBbox = [...editedElement.bbox] as [number, number, number, number];
    newBbox[index] = value;
    setEditedElement(prev => ({ ...prev, bbox: newBbox }));
  };

  const handleTextChange = (text: string) => {
    setEditedElement(prev => ({ ...prev, text }));
  };

  const handleConfidenceChange = (confidence: number) => {
    setEditedElement(prev => ({ ...prev, confidence }));
  };

  const handleSave = () => {
    // Validate element
    if (editedElement.bbox.some(val => val < 0)) {
      alert('Bounding box values must be non-negative');
      return;
    }

    if (editedElement.confidence < 0 || editedElement.confidence > 1) {
      alert('Confidence must be between 0 and 1');
      return;
    }

    onSave(editedElement);
  };

  return (
    <Card className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Edit Element</h3>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" onClick={onCancel}>
            <X className="h-4 w-4" />
          </Button>
          <Button size="sm" onClick={handleSave}>
            <Save className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Element ID */}
      <div className="space-y-2">
        <Label>Element ID</Label>
        <Input
          value={editedElement.id}
          disabled
          className="bg-gray-100"
        />
      </div>

      {/* Element Type */}
      <div className="space-y-2">
        <Label>Type</Label>
        <Input
          value={editedElement.type}
          disabled
          className="bg-gray-100"
        />
      </div>

      {/* Text Content */}
      {editedElement.type === 'text' && (
        <div className="space-y-2">
          <Label>Text Content</Label>
          <Input
            value={editedElement.text || ''}
            onChange={(e) => handleTextChange(e.target.value)}
            placeholder="Enter text content"
          />
        </div>
      )}

      {/* Bounding Box */}
      <div className="space-y-2">
        <Label>Bounding Box</Label>
        <div className="grid grid-cols-4 gap-2">
          <div>
            <Label className="text-xs">X</Label>
            <Input
              type="number"
              value={editedElement.bbox[0]}
              onChange={(e) => handleBboxChange(0, parseInt(e.target.value) || 0)}
              min="0"
            />
          </div>
          <div>
            <Label className="text-xs">Y</Label>
            <Input
              type="number"
              value={editedElement.bbox[1]}
              onChange={(e) => handleBboxChange(1, parseInt(e.target.value) || 0)}
              min="0"
            />
          </div>
          <div>
            <Label className="text-xs">Width</Label>
            <Input
              type="number"
              value={editedElement.bbox[2]}
              onChange={(e) => handleBboxChange(2, parseInt(e.target.value) || 0)}
              min="1"
            />
          </div>
          <div>
            <Label className="text-xs">Height</Label>
            <Input
              type="number"
              value={editedElement.bbox[3]}
              onChange={(e) => handleBboxChange(3, parseInt(e.target.value) || 0)}
              min="1"
            />
          </div>
        </div>
      </div>

      {/* Confidence */}
      <div className="space-y-2">
        <Label>Confidence: {editedElement.confidence.toFixed(2)}</Label>
        <Slider
          value={[editedElement.confidence]}
          max={1}
          step={0.01}
          onValueChange={([value]) => handleConfidenceChange(value)}
          className="w-full"
        />
      </div>

      {/* Visual Preview */}
      <div className="space-y-2">
        <Label>Preview</Label>
        <div className="relative w-full h-32 bg-gray-100 border rounded">
          <div
            className="absolute bg-blue-500 bg-opacity-50 border border-blue-500 rounded"
            style={{
              left: `${(editedElement.bbox[0] / 1000) * 100}%`,
              top: `${(editedElement.bbox[1] / 1000) * 100}%`,
              width: `${(editedElement.bbox[2] / 1000) * 100}%`,
              height: `${(editedElement.bbox[3] / 1000) * 100}%`
            }}
          >
            <div className="p-1 text-xs text-blue-700">
              {editedElement.text || editedElement.id}
            </div>
          </div>
        </div>
      </div>

      {/* Validation Messages */}
      {editedElement.bbox.some(val => val < 0) && (
        <div className="text-sm text-red-500">
          Bounding box values must be non-negative
        </div>
      )}
      
      {editedElement.confidence < 0.5 && (
        <div className="text-sm text-yellow-500">
          Low confidence score - consider reviewing this element
        </div>
      )}
    </Card>
  );
};
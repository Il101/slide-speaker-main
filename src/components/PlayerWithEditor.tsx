/**
 * Player Component Enhanced with Content Editor
 * 
 * Wrapper around existing Player that adds Content Editor functionality
 */
import React, { useState } from 'react';
import { Edit3 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Player } from '@/components/Player';
import { ContentEditor } from '@/components/ContentEditor';

interface PlayerWithEditorProps {
  lessonId: string;
  onExportMP4: () => void;
}

export const PlayerWithEditor: React.FC<PlayerWithEditorProps> = ({ 
  lessonId, 
  onExportMP4 
}) => {
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingSlide, setEditingSlide] = useState<number | null>(null);

  return (
    <>
      {/* Original Player */}
      <Player lessonId={lessonId} onExportMP4={onExportMP4} />

      {/* Floating Edit Button */}
      <div className="fixed bottom-24 right-6 z-50">
        <Button
          onClick={() => {
            // Get current slide from player state (would need to expose this)
            // For now, default to slide 1
            setEditingSlide(1);
            setEditorOpen(true);
          }}
          size="lg"
          className="shadow-lg"
        >
          <Edit3 className="h-5 w-5 mr-2" />
          Редактировать скрипт
        </Button>
      </div>

      {/* Content Editor Dialog */}
      <Dialog open={editorOpen} onOpenChange={setEditorOpen}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Редактор контента слайда</DialogTitle>
          </DialogHeader>
          {editingSlide && (
            <ContentEditor
              lessonId={lessonId}
              slideNumber={editingSlide}
              onSave={(newScript) => {
                console.log('Script updated:', newScript);
                // Optionally reload player manifest
                setEditorOpen(false);
              }}
              onClose={() => setEditorOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

import SignatureModal from "@/components/core/SignatureModal";

interface ESignatureModalProps {
  isOpen: boolean;
  isLoading?: boolean;
  title?: string;
  description?: string;
  onClose: () => void;
  onConfirm: (payload: {
    username: string;
    password: string;
    meaning: string;
    comments: string;
  }) => Promise<void>;
  meaning?: string;
  availableMeanings?: string[];
}

export default function ESignatureModal({
  isOpen,
  isLoading = false,
  title,
  description,
  onClose,
  onConfirm,
  meaning,
  availableMeanings,
}: ESignatureModalProps) {
  return (
    <SignatureModal
      isOpen={isOpen}
      isLoading={isLoading}
      title={title}
      description={description}
      meaning={meaning}
      availableMeanings={availableMeanings}
      onClose={onClose}
      onConfirm={async (username, password, selectedMeaning, comments) =>
        onConfirm({ username, password, meaning: selectedMeaning, comments })
      }
    />
  );
}

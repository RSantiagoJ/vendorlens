"use client";

import { useRef, useState } from "react";
import {
  Paper, Text, Stack, Group, Button, ActionIcon, ThemeIcon,
  SegmentedControl, Box,
} from "@mantine/core";
import {
  IconUpload, IconFile, IconX, IconFileAnalytics,
  IconDeviceLaptop, IconShieldLock,
} from "@tabler/icons-react";
import type { Bundle } from "@/lib/types";

const BUNDLE_ICONS: Record<string, React.ReactNode> = {
  lms: <IconDeviceLaptop size={14} />,
  cyber: <IconShieldLock size={14} />,
};

interface Props {
  onSubmit: (files: File[], bundle: string) => void;
  loading: boolean;
  bundles: Bundle[];
}

export function UploadZone({ onSubmit, loading, bundles }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [bundle, setBundle] = useState(bundles[0]?.id ?? "lms");
  const inputRef = useRef<HTMLInputElement>(null);

  function addFiles(incoming: FileList | null) {
    if (!incoming) return;
    const next = Array.from(incoming).filter(
      (f) => !files.some((existing) => existing.name === f.name)
    );
    setFiles((prev) => [...prev, ...next]);
  }

  function removeFile(name: string) {
    setFiles((prev) => prev.filter((f) => f.name !== name));
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  }

  const selectedBundle = bundles.find((b) => b.id === bundle);

  return (
    <Stack gap="md" w="100%" maw={640} mx="auto">
      {/* RFP selector */}
      <Paper p="md" radius="md" withBorder bg="white">
        <Stack gap="xs">
          <Text size="sm" fw={600} c="dark">Evaluation Framework</Text>
          <SegmentedControl
            value={bundle}
            onChange={setBundle}
            data={bundles.map((b) => ({
              value: b.id,
              label: (
                <Group gap={6} justify="center" wrap="nowrap">
                  {BUNDLE_ICONS[b.id]}
                  <span>{b.label}</span>
                </Group>
              ),
            }))}
            color="umgreen"
            radius="md"
            fullWidth
          />
          {selectedBundle && (
            <Text size="xs" c="dimmed">{selectedBundle.description}</Text>
          )}
        </Stack>
      </Paper>

      {/* Drop zone */}
      <Paper
        p="xl"
        radius="md"
        withBorder
        style={{
          borderStyle: "dashed",
          borderWidth: 2,
          borderColor: dragging
            ? "var(--mantine-color-umgreen-6)"
            : "var(--mantine-color-gray-4)",
          cursor: "pointer",
          background: dragging ? "var(--mantine-color-umgreen-0)" : "white",
          transition: "border-color 120ms ease, background 120ms ease",
        }}
        onClick={() => !loading && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <Stack align="center" gap="sm">
          <ThemeIcon size={56} radius="xl" variant="light" color="umgreen">
            <IconUpload size={28} />
          </ThemeIcon>
          <Text fw={600} size="lg" c="dark">Drop vendor proposals here</Text>
          <Text c="dimmed" size="sm" ta="center">
            Drag and drop .txt or .pdf files, or click to browse
          </Text>
        </Stack>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".txt,.pdf"
          style={{ display: "none" }}
          onChange={(e) => addFiles(e.target.files)}
        />
      </Paper>

      {/* File list */}
      {files.length > 0 && (
        <Stack gap="xs">
          {files.map((f) => (
            <Paper key={f.name} px="md" py="sm" radius="md" withBorder bg="white">
              <Group justify="space-between" gap="sm">
                <Group gap="sm">
                  <ThemeIcon size={32} radius="md" variant="light" color="umblue">
                    <IconFile size={16} />
                  </ThemeIcon>
                  <Text size="sm" fw={500} c="dark" style={{ wordBreak: "break-all" }}>
                    {f.name}
                  </Text>
                </Group>
                <ActionIcon
                  variant="subtle"
                  color="gray"
                  size="sm"
                  onClick={() => removeFile(f.name)}
                  aria-label={`Remove ${f.name}`}
                >
                  <IconX size={14} />
                </ActionIcon>
              </Group>
            </Paper>
          ))}
        </Stack>
      )}

      <Button
        leftSection={<IconFileAnalytics size={18} />}
        size="md"
        radius="md"
        color="umgreen"
        loading={loading}
        disabled={files.length === 0}
        onClick={() => onSubmit(files, bundle)}
        fullWidth
      >
        Analyze {files.length > 0 ? `${files.length} proposal${files.length > 1 ? "s" : ""}` : "proposals"}
      </Button>
    </Stack>
  );
}

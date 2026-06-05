"use client";

import {
  Paper, Group, Text, Button, Divider, ScrollArea,
  Title, Table, Stack,
} from "@mantine/core";
import { IconDownload, IconFileText, IconPrinter } from "@tabler/icons-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  memo: string;
}

const mdComponents: React.ComponentProps<typeof ReactMarkdown>["components"] = {
  h1: ({ children }) => (
    <Title order={2} mb="sm" mt="lg" c="dark">{children}</Title>
  ),
  h2: ({ children }) => (
    <Title order={3} mb="xs" mt="md" c="dark">{children}</Title>
  ),
  h3: ({ children }) => (
    <Title order={4} mb="xs" mt="sm" c="dark">{children}</Title>
  ),
  p: ({ children }) => (
    <Text component="div" mb="sm" size="sm" lh={1.75} c="dark.7">{children}</Text>
  ),
  strong: ({ children }) => (
    <Text component="strong" fw={600} c="dark.8">{children}</Text>
  ),
  em: ({ children }) => (
    <Text component="em" fs="italic" c="dimmed">{children}</Text>
  ),
  ul: ({ children }) => (
    <Stack component="ul" gap={4} mb="sm" pl="lg" style={{ listStyle: "disc" }}>
      {children}
    </Stack>
  ),
  ol: ({ children }) => (
    <Stack component="ol" gap={4} mb="sm" pl="lg" style={{ listStyle: "decimal" }}>
      {children}
    </Stack>
  ),
  li: ({ children }) => (
    <Text component="li" size="sm" lh={1.7} c="dark.7">{children}</Text>
  ),
  hr: () => <Divider my="md" />,
  table: ({ children }) => (
    <Table
      mb="md"
      withTableBorder
      withColumnBorders
      striped
      highlightOnHover
      style={{ fontSize: "0.8rem" }}
    >
      {children}
    </Table>
  ),
  thead: ({ children }) => <Table.Thead>{children}</Table.Thead>,
  tbody: ({ children }) => <Table.Tbody>{children}</Table.Tbody>,
  tr: ({ children }) => <Table.Tr>{children}</Table.Tr>,
  th: ({ children }) => (
    <Table.Th style={{ whiteSpace: "nowrap", background: "var(--mantine-color-gray-1)" }}>
      {children}
    </Table.Th>
  ),
  td: ({ children }) => <Table.Td>{children}</Table.Td>,
  blockquote: ({ children }) => (
    <Paper
      withBorder
      p="sm"
      mb="sm"
      radius="sm"
      style={{ borderLeft: "3px solid var(--mantine-color-umgreen-5)", background: "var(--mantine-color-gray-0)" }}
    >
      <Text component="div" size="sm" c="dimmed" fs="italic">{children}</Text>
    </Paper>
  ),
};

export function MemoPanel({ memo }: Props) {
  function download() {
    const blob = new Blob([memo], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "vendorlens-recommendation.md";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Paper p="lg" radius="md" withBorder bg="white" className="fadeIn" style={{ borderLeft: "4px solid var(--mantine-color-umgreen-5)" }}>
      <Group justify="space-between" align="center" mb="md">
        <Group gap="sm">
          <IconFileText size={20} color="var(--mantine-color-umgreen-6)" />
          <Text fw={700} size="lg" c="dark">
            Recommendation Memo
          </Text>
        </Group>
        <Group gap="xs">
          <Button
            leftSection={<IconPrinter size={16} />}
            variant="outline"
            color="umgreen"
            size="sm"
            radius="md"
            data-print-hide
            onClick={() => window.print()}
          >
            Save as PDF
          </Button>
          <Button
            leftSection={<IconDownload size={16} />}
            variant="outline"
            color="umblue"
            size="sm"
            radius="md"
            data-print-hide
            onClick={download}
          >
            Download .md
          </Button>
        </Group>
      </Group>
      <Divider mb="md" />
      <ScrollArea.Autosize mah={600}>
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
          {memo}
        </ReactMarkdown>
      </ScrollArea.Autosize>
    </Paper>
  );
}

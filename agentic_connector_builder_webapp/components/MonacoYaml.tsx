import React, { useMemo } from "react";
import Editor, { OnMount, BeforeMount } from "@monaco-editor/react";
import * as monacoEditor from "monaco-editor";
import { configureMonacoYaml, type DiagnosticsOptions } from "monaco-yaml";

export type SchemaAssociation = {
  uri?: string;
  fileMatch?: string[];
  schema?: any;
};

export type MonacoYamlProps = {
  value?: string;
  height?: string | number;
  readOnly?: boolean;
  schemas?: SchemaAssociation[];
  enableSchemaRequest?: boolean;
  yamlVersion?: "1.1" | "1.2";
  completion?: boolean;
  hover?: boolean;
  format?: boolean;
  validate?: boolean;
  isKubernetes?: boolean;
  language?: string;
  onChange?: (val: string) => void;
};

const MonacoYaml: React.FC<MonacoYamlProps> = ({
  value = "",
  height = "500px",
  readOnly = false,
  schemas = [],
  enableSchemaRequest = false,
  yamlVersion = "1.2",
  completion = true,
  hover = true,
  format = true,
  validate = true,
  isKubernetes = false,
  language = "yaml",
  onChange,
}) => {
  const options = useMemo<DiagnosticsOptions>(() => ({
    enableSchemaRequest,
    yamlVersion,
    completion,
    hover,
    format,
    validate,
    isKubernetes,
    schemas,
  }), [enableSchemaRequest, yamlVersion, completion, hover, format, validate, isKubernetes, schemas]);

  const beforeMount: BeforeMount = (monaco) => {
    configureMonacoYaml(monaco as unknown as typeof monacoEditor, options);
  };

  const onMount: OnMount = (editor, monaco) => {
    editor.updateOptions({ readOnly });
  };

  return (
    <Editor
      defaultLanguage={language}
      defaultValue={value}
      beforeMount={beforeMount}
      onMount={onMount}
      onChange={(v) => onChange?.(v ?? "")}
      height={height}
      options={{
        readOnly,
        automaticLayout: true,
        minimap: { enabled: false },
        wordWrap: "on",
        fontSize: 14,
        lineNumbers: "on",
        roundedSelection: false,
        scrollBeyondLastLine: false,
        tabSize: 2,
        insertSpaces: true,
      }}
    />
  );
};

export default MonacoYaml;

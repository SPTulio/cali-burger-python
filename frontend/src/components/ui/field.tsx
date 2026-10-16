import { createContext, useContext, useId, type ComponentProps, type ReactNode } from "react";

import { cn } from "@/lib/utils";

interface FieldContextValue {
  id: string;
  errorId: string;
  descriptionId: string;
  invalid: boolean;
  hasDescription: boolean;
}

const FieldContext = createContext<FieldContextValue | null>(null);

/** Liga rótulo, descrição e erro ao controle (id, aria-invalid, aria-describedby). */
export function useFieldControl(props: { id?: string; "aria-describedby"?: string }) {
  const field = useContext(FieldContext);
  if (!field) return { id: props.id };
  const describedBy = [
    props["aria-describedby"],
    field.hasDescription ? field.descriptionId : null,
    field.invalid ? field.errorId : null,
  ]
    .filter(Boolean)
    .join(" ");
  return {
    id: props.id ?? field.id,
    "aria-invalid": field.invalid || undefined,
    "aria-describedby": describedBy || undefined,
  };
}

interface FieldProps {
  label: ReactNode;
  error?: string;
  description?: ReactNode;
  className?: string;
  children: ReactNode;
  required?: boolean;
  id?: string;
}

export function Field({ label, error, description, className, children, required, id }: FieldProps) {
  const generated = useId();
  const fieldId = id ?? `field-${generated}`;
  const value: FieldContextValue = {
    id: fieldId,
    errorId: `${fieldId}-error`,
    descriptionId: `${fieldId}-description`,
    invalid: Boolean(error),
    hasDescription: Boolean(description),
  };
  return (
    <FieldContext.Provider value={value}>
      <div className={cn("flex flex-col gap-1.5", className)}>
        <label htmlFor={fieldId} className="text-[13px] font-medium text-foreground">
          {label}
          {required && (
            <span className="text-destructive" aria-hidden>
              {" "}
              *
            </span>
          )}
        </label>
        {children}
        {description && !error && (
          <p id={value.descriptionId} className="text-xs text-muted-foreground">
            {description}
          </p>
        )}
        {error && (
          <p id={value.errorId} className="text-xs font-medium text-destructive">
            {error}
          </p>
        )}
      </div>
    </FieldContext.Provider>
  );
}

const controlBase =
  "w-full rounded-md border border-input bg-surface px-3 text-sm text-foreground shadow-xs transition-colors placeholder:text-muted-foreground/80 focus-visible:border-ring focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-ring/30 disabled:cursor-not-allowed disabled:opacity-60 aria-invalid:border-destructive aria-invalid:focus-visible:outline-destructive/30";

export function Input({ className, ...props }: ComponentProps<"input">) {
  const control = useFieldControl(props);
  return <input className={cn(controlBase, "h-9", className)} {...props} {...control} />;
}

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  const control = useFieldControl(props);
  return (
    <textarea className={cn(controlBase, "min-h-20 py-2", className)} {...props} {...control} />
  );
}

/** Select nativo estilizado: acessível, rápido e com o seletor do próprio celular. */
export function Select({ className, children, ...props }: ComponentProps<"select">) {
  const control = useFieldControl(props);
  return (
    <select
      className={cn(
        controlBase,
        "h-9 appearance-none bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2216%22 height=%2216%22 fill=%22none%22 stroke=%22%2378716c%22 stroke-width=%222%22 viewBox=%220 0 24 24%22><path d=%22m6 9 6 6 6-6%22/></svg>')] bg-[length:16px] bg-[right_10px_center] bg-no-repeat pr-9",
        className,
      )}
      {...props}
      {...control}
    >
      {children}
    </select>
  );
}

export function FormError({ message }: { message?: string | null }) {
  if (!message) return null;
  return (
    <div
      role="alert"
      className="rounded-md border border-destructive/30 bg-destructive-soft px-3 py-2.5 text-sm text-destructive"
    >
      {message}
    </div>
  );
}

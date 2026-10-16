import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ImagePlus, Plus, Trash, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router";
import { toast } from "sonner";
import { z } from "zod";

import { errorMessage } from "@/api/client";
import { catalogApi, inventoryApi } from "@/api/endpoints";
import { queryKeys } from "@/api/keys";
import { ErrorState, PageHeader } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { Card, CardHeader, Skeleton } from "@/components/ui/primitives";
import { applyApiErrors, fields } from "@/lib/validation";
import type { MenuItem } from "@/types/api";

const MAX_IMAGE_BYTES = 2 * 1024 * 1024;
const IMAGE_TYPES = ["image/png", "image/jpeg", "image/webp"];

const schema = z.object({
  name: fields.required(100),
  description: fields.optional(255),
  price: z
    .string()
    .trim()
    .min(1, "Informe o preço.")
    .regex(/^\d{1,4}([.,]\d{1,2})?$/, "Informe um preço válido, por exemplo 22,90.")
    .refine((v) => Number(v.replace(",", ".")) > 0, "O preço deve ser maior que zero."),
  category_id: z.string().min(1, "Selecione uma categoria."),
  recipe: z
    .array(
      z.object({
        ingredient_id: z.string().min(1, "Selecione o ingrediente."),
        quantity: z.coerce.number<string>().int("Use um número inteiro.").min(1, "Mínimo 1.").max(1000, "Máximo 1000."),
      }),
    )
    .refine(
      (lines) => new Set(lines.map((l) => l.ingredient_id)).size === lines.length,
      "Cada ingrediente pode aparecer só uma vez.",
    ),
});
type FormInput = z.input<typeof schema>;
type FormOutput = z.output<typeof schema>;

function toForm(item?: MenuItem): FormInput {
  return {
    name: item?.name ?? "",
    description: item?.description ?? "",
    price: item ? item.price.replace(".", ",") : "",
    category_id: item ? String(item.category.id) : "",
    recipe: (item?.recipe ?? []).map((r) => ({ ingredient_id: String(r.ingredient_id), quantity: String(r.quantity) })),
  };
}

export function MenuItemFormPage() {
  const params = useParams();
  const id = params.id ? Number(params.id) : null;
  const item = useQuery({
    queryKey: queryKeys.menuItem(id ?? 0),
    queryFn: () => catalogApi.item(id!),
    enabled: id !== null,
  });

  if (id !== null && item.isPending) return <Skeleton className="h-[480px]" />;
  if (id !== null && item.isError) return <ErrorState error={item.error} onRetry={() => item.refetch()} />;
  return <MenuItemForm key={id ?? "novo"} item={item.data} />;
}

function MenuItemForm({ item }: { item?: MenuItem }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const categories = useQuery({ queryKey: queryKeys.categories, queryFn: catalogApi.categories, staleTime: Infinity });
  const ingredients = useQuery({ queryKey: queryKeys.inventory(), queryFn: () => inventoryApi.list() });

  const form = useForm<FormInput, unknown, FormOutput>({ resolver: zodResolver(schema), defaultValues: toForm(item) });
  const recipe = useFieldArray({ control: form.control, name: "recipe" });
  const recipeValues = useWatch({ control: form.control, name: "recipe" });
  const { errors } = form.formState;

  const [file, setFile] = useState<File | null>(null);
  const [removeImage, setRemoveImage] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const preview = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => () => void (preview && URL.revokeObjectURL(preview)), [preview]);
  const currentImage = removeImage ? null : (preview ?? item?.image_url ?? null);

  function pickFile(selected: File | undefined) {
    setFileError(null);
    if (!selected) return;
    if (!IMAGE_TYPES.includes(selected.type)) return setFileError("Envie uma imagem PNG, JPG ou WebP.");
    if (selected.size > MAX_IMAGE_BYTES) return setFileError("A imagem deve ter no máximo 2 MB.");
    setFile(selected);
    setRemoveImage(false);
  }

  const save = useMutation({
    mutationFn: async (data: FormOutput) => {
      const payload = {
        name: data.name,
        description: data.description || null,
        price: data.price.replace(",", "."),
        category_id: Number(data.category_id),
        recipe: data.recipe.map((r) => ({ ingredient_id: Number(r.ingredient_id), quantity: r.quantity })),
      };
      const saved = item ? await catalogApi.update(item.id, payload) : await catalogApi.create(payload);
      try {
        if (file) await catalogApi.uploadImage(saved.id, file);
        else if (removeImage && item?.image_url) await catalogApi.removeImage(saved.id);
      } catch (error) {
        // O item foi salvo; só a imagem falhou. Leva para a edição para tentar de novo.
        toast.error(`Item salvo, mas a imagem não foi enviada: ${errorMessage(error)}`);
        return { saved, imageFailed: true };
      }
      return { saved, imageFailed: false };
    },
    onSuccess: ({ saved, imageFailed }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.menuAll });
      queryClient.invalidateQueries({ queryKey: queryKeys.inventoryAll });
      if (imageFailed) {
        navigate(`/painel/cardapio/${saved.id}`, { replace: true });
        return;
      }
      toast.success(item ? "Item atualizado." : "Item adicionado ao cardápio.");
      navigate("/painel/cardapio");
    },
    onError: (error) => {
      if (!applyApiErrors(error, form.setError)) toast.error(errorMessage(error));
    },
  });

  const ingredientOptions = ingredients.data?.items ?? [];
  const stockById = new Map(ingredientOptions.map((i) => [String(i.id), i]));

  return (
    <div className="mx-auto max-w-3xl">
      <Button asChild variant="ghost" size="sm" className="-ml-3 mb-4">
        <Link to="/painel/cardapio">
          <ArrowLeft /> Cardápio
        </Link>
      </Button>
      <PageHeader title={item ? `Editar ${item.name}` : "Novo item do cardápio"} />

      <form className="flex flex-col gap-6" onSubmit={form.handleSubmit((d) => save.mutate(d))} noValidate>
        <Card>
          <CardHeader title="Informações" />
          <div className="grid gap-4 p-5 sm:grid-cols-2">
            <Field label="Nome" error={errors.name?.message} className="sm:col-span-2" required>
              <Input {...form.register("name")} />
            </Field>
            <Field label="Descrição" error={errors.description?.message} className="sm:col-span-2" description="Aparece no cardápio do cliente (até 255 caracteres).">
              <Textarea rows={2} maxLength={255} {...form.register("description")} />
            </Field>
            <Field label="Categoria" error={errors.category_id?.message} required>
              <Select {...form.register("category_id")}>
                <option value="">Selecione</option>
                {categories.data?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Preço (R$)" error={errors.price?.message} required>
              <Input inputMode="decimal" placeholder="22,90" {...form.register("price")} />
            </Field>
          </div>
        </Card>

        <Card>
          <CardHeader title="Imagem" description="PNG, JPG ou WebP, até 2 MB." />
          <div className="flex flex-wrap items-center gap-5 p-5">
            <div className="flex size-28 items-center justify-center overflow-hidden rounded-lg border bg-muted">
              {currentImage ? (
                <img src={currentImage} alt="Pré-visualização" className="size-full object-cover" />
              ) : (
                <ImagePlus className="size-7 text-muted-foreground" aria-hidden />
              )}
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex flex-wrap gap-2">
                <Button asChild variant="outline">
                  <label className="cursor-pointer">
                    <ImagePlus /> {currentImage ? "Trocar imagem" : "Escolher imagem"}
                    <input
                      type="file"
                      accept={IMAGE_TYPES.join(",")}
                      className="sr-only"
                      onChange={(e) => pickFile(e.target.files?.[0])}
                    />
                  </label>
                </Button>
                {currentImage && (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setFile(null);
                      setRemoveImage(Boolean(item?.image_url));
                    }}
                  >
                    <X /> Remover
                  </Button>
                )}
              </div>
              {fileError ? (
                <p className="text-xs font-medium text-destructive" role="alert">{fileError}</p>
              ) : (
                (file || removeImage) && <p className="text-xs text-muted-foreground">A alteração é aplicada ao salvar.</p>
              )}
              {errors.root?.message && <p className="text-xs text-destructive">{errors.root.message}</p>}
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Receita"
            description="Ingredientes usados em uma unidade. O estoque é descontado a cada pedido; sem receita, o item não depende do estoque."
          />
          <div className="flex flex-col gap-3 p-5">
            {recipe.fields.length === 0 && (
              <p className="text-sm text-muted-foreground">Nenhum ingrediente na receita.</p>
            )}
            {recipe.fields.map((line, index) => {
              const selected = stockById.get(recipeValues?.[index]?.ingredient_id ?? "");
              return (
                <div key={line.id} className="grid grid-cols-[1fr_96px_36px] items-start gap-2">
                  <Field label="Ingrediente" error={errors.recipe?.[index]?.ingredient_id?.message} className="[&>label]:sr-only">
                    <Select {...form.register(`recipe.${index}.ingredient_id`)}>
                      <option value="">Selecione o ingrediente</option>
                      {ingredientOptions.map((ing) => (
                        <option key={ing.id} value={ing.id}>
                          {ing.name} — {ing.quantity} em estoque
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Field label="Quantidade" error={errors.recipe?.[index]?.quantity?.message} className="[&>label]:sr-only">
                    <Input type="number" min={1} max={1000} aria-label={`Quantidade de ${selected?.name ?? "ingrediente"}`} {...form.register(`recipe.${index}.quantity`)} />
                  </Field>
                  <Button variant="ghost" size="icon" onClick={() => recipe.remove(index)} aria-label="Remover ingrediente">
                    <Trash className="text-muted-foreground" />
                  </Button>
                </div>
              );
            })}
            {errors.recipe?.root?.message && <p className="text-xs font-medium text-destructive">{errors.recipe.root.message}</p>}
            {errors.recipe?.message && <p className="text-xs font-medium text-destructive">{errors.recipe.message}</p>}
            <div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => recipe.append({ ingredient_id: "", quantity: "1" })}
                disabled={ingredients.isPending || recipe.fields.length >= ingredientOptions.length}
              >
                <Plus /> Adicionar ingrediente
              </Button>
              {ingredientOptions.length === 0 && !ingredients.isPending && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Cadastre ingredientes em <Link to="/painel/estoque" className="text-primary hover:underline">Estoque</Link>.
                </p>
              )}
            </div>
          </div>
        </Card>

        <div className="flex justify-end gap-2">
          <Button asChild variant="outline">
            <Link to="/painel/cardapio">Cancelar</Link>
          </Button>
          <Button type="submit" loading={save.isPending}>
            {item ? "Salvar alterações" : "Adicionar ao cardápio"}
          </Button>
        </div>
      </form>
    </div>
  );
}

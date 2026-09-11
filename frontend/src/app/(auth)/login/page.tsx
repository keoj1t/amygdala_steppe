"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import "@/i18n/client";
import { api } from "@/lib/api";
import type { TokenPair } from "@/lib/types";
import { useAuthStore } from "@/store/auth-store";
import { useToastStore } from "@/store/toast-store";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const { t } = useTranslation();
  const { setSession } = useAuthStore();
  const { push } = useToastStore();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" }
  });

  async function onSubmit(values: FormValues) {
    try {
      const { data } = await api.post<TokenPair>("/api/v1/auth/login", values);
      setSession(data);
      router.push("/dashboard");
    } catch (error) {
      push({ title: error instanceof Error ? error.message : "Login failed", tone: "error" });
    }
  }

  return (
    <section className="w-[min(100%,420px)] rounded-2xl border border-white/15 bg-black p-6 shadow-2xl">
      <div className="mb-6">
        <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-orange text-sm font-black text-white">AI</div>
        <h1 className="text-2xl font-bold text-white">{t("auth.login")}</h1>
        <p className="mt-1 text-sm text-white/45">amygdala content factory</p>
      </div>
      <form className="grid gap-4" onSubmit={form.handleSubmit(onSubmit)}>
        <Input placeholder={t("auth.email")} type="email" {...form.register("email")} />
        <Input placeholder={t("auth.password")} type="password" {...form.register("password")} />
        <Button type="submit" disabled={form.formState.isSubmitting}>{t("auth.login")}</Button>
      </form>
      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-white/45">{t("auth.noAccount")}</span>
        <Link href="/register" className="font-semibold text-[#CC5500]">{t("auth.register")}</Link>
      </div>
    </section>
  );
}

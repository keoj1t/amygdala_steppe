"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import "@/i18n/client";
import { api } from "@/lib/api";
import { useToastStore } from "@/store/toast-store";

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
});

const verifySchema = z.object({
  code: z.string().regex(/^\d{6}$/)
});

type RegisterValues = z.infer<typeof registerSchema>;
type VerifyValues = z.infer<typeof verifySchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { t } = useTranslation();
  const { push } = useToastStore();
  const [email, setEmail] = useState("");
  const [otpOpen, setOtpOpen] = useState(false);
  const registerForm = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: "", password: "" }
  });
  const verifyForm = useForm<VerifyValues>({
    resolver: zodResolver(verifySchema),
    defaultValues: { code: "" }
  });

  async function onRegister(values: RegisterValues) {
    try {
      await api.post("/api/v1/auth/register", values);
      setEmail(values.email);
      setOtpOpen(true);
      push({ title: t("auth.sent"), tone: "success" });
    } catch (error) {
      push({ title: error instanceof Error ? error.message : "Registration failed", tone: "error" });
    }
  }

  async function onVerify(values: VerifyValues) {
    try {
      await api.post("/api/v1/auth/verify-email", { email, code: values.code });
      push({ title: "Email verified", tone: "success" });
      router.push("/login");
    } catch (error) {
      push({ title: error instanceof Error ? error.message : "Verification failed", tone: "error" });
    }
  }

  return (
    <section className="w-[min(100%,420px)] rounded-2xl border border-white/15 bg-black p-6 shadow-2xl">
      <div className="mb-6">
        <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-orange text-sm font-black text-white">AI</div>
        <h1 className="text-2xl font-bold text-white">{t("auth.register")}</h1>
        <p className="mt-1 text-sm text-white/45">amygdala content factory</p>
      </div>
      <form className="grid gap-4" onSubmit={registerForm.handleSubmit(onRegister)}>
        <div className="grid gap-1">
          <Input placeholder={t("auth.email")} type="email" {...registerForm.register("email")} />
          {registerForm.formState.errors.email && (
            <p className="text-xs text-red-600">Введите корректную почту.</p>
          )}
        </div>
        <div className="grid gap-1">
          <Input placeholder={t("auth.password")} type="password" {...registerForm.register("password")} />
          {registerForm.formState.errors.password && (
            <p className="text-xs text-red-600">Пароль должен содержать минимум 8 символов.</p>
          )}
        </div>
        <Button type="submit" disabled={registerForm.formState.isSubmitting}>{t("auth.register")}</Button>
      </form>
      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-white/45">{t("auth.hasAccount")}</span>
        <Link href="/login" className="font-semibold text-[#CC5500]">{t("auth.login")}</Link>
      </div>
      <Modal open={otpOpen} onOpenChange={setOtpOpen} title={t("auth.verify")}>
        <form className="grid gap-4" onSubmit={verifyForm.handleSubmit(onVerify)}>
          <Input inputMode="numeric" maxLength={6} placeholder={t("auth.code")} {...verifyForm.register("code")} />
          <Button type="submit" disabled={verifyForm.formState.isSubmitting}>{t("auth.verify")}</Button>
        </form>
      </Modal>
    </section>
  );
}

"use client";
import React, { useState } from "react";
// import Layout from "../../../layout/website";
// import Section from "../../../layout/global/Section";
// import Container from "../../../layout/global/Container";

// import { Label, Input, Button } from "../../../components";
// import axiosInstance from "../../../lib/axios";
import { useRouter } from "next/navigation";
import { Facebook } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginSchema } from "@/data/schema/loginSchema";
import { z } from "zod";

function LoginPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };
  const onSubmit = async (values: z.infer<typeof loginSchema>) => {
    if (formData.email.trim() == "" || formData.password.trim() == "") {
      return alert("Please enter email and password");
    }
    // try {
    //   const response = await axiosInstance.post(
    //     "/login",
    //     // "http://localhost:8000/login",
    //     formData
    //   );
    //   alert(response.data.message);
    //   console.log(response);

    //   // get the name of the user
    //   const user = response.data.user;
    //   // Store user info in localStorage or state management
    //   localStorage.setItem("user", JSON.stringify(response.data.user));

    //   // Call onLogin to update App state
    //   //   onLogin(user);

    //   router.replace("/"); // Redirect to dashboard or home page
    // } catch (error) {
    //   console.log(error);

    //   alert(error.response?.data?.detail || "Login failed");
    // }
  };

  const form = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  return (
        <div className="max-w-md w-full rounded-lg border border-slate-200 bg-white p-6 pt-5 dark:border-slate-800 dark:bg-slate-950">
          <div className="mb-2">
            <h3 className="mb-1 text-xl font-bold text-slate-700 dark:text-white">
              Login
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              With valid credentials
            </p>
          </div>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)}>
              <div className="space-y-5 mb-10">
                <FormField
                  control={form.control}
                  name="email"
                  render={() => (
                    <FormItem>
                      <FormLabel htmlFor="emial-address">
                        Email Address
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder="example@email.com"
                          id="emial-address"
                          name="email"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="password"
                  render={() => (
                    <FormItem>
                      <FormLabel htmlFor="password">Password</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="********"
                          id="password"
                          name="password"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div>
                <Button className="w-full bg-blue-600 text-white hover:bg-blue-800">
                  Account Login
                </Button>
              </div>
            </form>
          </Form>

          <div className="mb-4 mt-5">
            <h6 className="text-center text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Login With
            </h6>
          </div>
          <div className="-mx-3 flex flex-wrap">
            <div className="w-1/2 px-3">
              <Button
                className="flex gap-2 w-full text-primary hover:text-primary"
                variant={"outline"}
              >
                {/* <Google */}
                <span>Google</span>
              </Button>
            </div>
            <div className="w-1/2 px-3">
              <Button
                className="flex gap-2 w-full text-primary hover:text-primary"
                variant={"outline"}
              >
                <Facebook className="w-4 h-4" />
                <span>Facebook</span>
              </Button>
            </div>
          </div>
        </div>
  );
}

export default LoginPage;

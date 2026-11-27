"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Loader2,
  Bot,
  User,
  CheckCircle2,
  MapPin,
  Plus,
  X,
  Send,
  Building,
  Home,
} from "lucide-react";
import { ChatMessage, AddressItem } from "@/types/chat";

interface MessageItemProps {
  message: ChatMessage;
  onAddToCart: (id: number) => void;
  onSendQuery: (query: string) => void;
}

/**
 * Extracts delivery addresses either from structured message.addresses
 * or from raw message text (fallback for existing chat history).
 */
function extractAddresses(message: ChatMessage): AddressItem[] {
  if (message.addresses && message.addresses.length > 0) {
    return message.addresses;
  }

  const content = message.content || "";
  if (!content.toLowerCase().includes("saved delivery address") && !content.includes("Recipient:")) {
    return [];
  }

  const items: AddressItem[] = [];
  const lines = content.split("\n");
  let current: Partial<AddressItem> | null = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    const numMatch = line.match(/^(\d+)\.\s*\*?\*?([^*]+)\*?\*?/);
    if (numMatch && !line.toLowerCase().includes("items:")) {
      if (current && current.recipient_name && current.address) {
        items.push({
          id: current.id || items.length + 1,
          title: current.title || `Address #${items.length + 1}`,
          recipient_name: current.recipient_name,
          phone: current.phone || "",
          address: current.address,
        });
      }
      current = {
        id: parseInt(numMatch[1]),
        title: numMatch[2].replace(/:$/, "").trim(),
      };
      continue;
    }

    if (current) {
      if (line.toLowerCase().startsWith("recipient:")) {
        current.recipient_name = line.replace(/^[Rr]ecipient:\s*/, "").replace(/\*\*/g, "").trim();
      } else if (line.toLowerCase().startsWith("address:")) {
        current.address = line.replace(/^[Aa]ddress:\s*/, "").replace(/\*\*/g, "").trim();
      } else if (line.toLowerCase().startsWith("phone:")) {
        current.phone = line.replace(/^[Pp]hone:\s*/, "").replace(/\*\*/g, "").trim();
      }
    }
  }

  if (current && current.recipient_name && current.address) {
    items.push({
      id: current.id || items.length + 1,
      title: current.title || `Address #${items.length + 1}`,
      recipient_name: current.recipient_name,
      phone: current.phone || "",
      address: current.address,
    });
  }

  return items;
}

export function MessageItem({ message, onAddToCart, onSendQuery }: MessageItemProps) {
  const isUser = message.role === "user";
  const [showAddForm, setShowAddForm] = useState(false);
  const [formError, setFormError] = useState("");

  const [formData, setFormData] = useState({
    recipient_name: "",
    phone: "",
    address_line: "",
    city: "",
    state: "",
    pincode: "",
    title: "Home",
  });

  const addresses = !isUser ? extractAddresses(message) : [];

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
    if (formError) setFormError("");
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !formData.recipient_name.trim() ||
      !formData.phone.trim() ||
      !formData.address_line.trim() ||
      !formData.pincode.trim()
    ) {
      setFormError("Please fill in Name, Phone, Address, and Pincode.");
      return;
    }

    const cityPart = formData.city.trim() ? `${formData.city.trim()}, ` : "";
    const statePart = formData.state.trim() ? `${formData.state.trim()} - ` : "";
    const fullAddress = `${formData.address_line.trim()}, ${cityPart}${statePart}${formData.pincode.trim()}`;

    const query = `Please deliver to my new address: ${formData.recipient_name.trim()}, ${fullAddress} (Phone: ${formData.phone.trim()}). Save this address as ${formData.title}.`;
    onSendQuery(query);

    setShowAddForm(false);
    setFormData({
      recipient_name: "",
      phone: "",
      address_line: "",
      city: "",
      state: "",
      pincode: "",
      title: "Home",
    });
  };

  return (
    <div className={`flex gap-3.5 w-full ${isUser ? "flex-row-reverse" : "flex-row"} animate-fadeIn`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold ${
          isUser
            ? "bg-gray-700 text-gray-200"
            : "bg-gradient-to-tr from-indigo-500 to-purple-600 text-white shadow-md shadow-indigo-500/25"
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Bubble Container */}
      <div className={`flex flex-col gap-2 max-w-[85%] ${isUser ? "items-end" : "items-start"}`}>
        {/* Tool Activity Badges (Shows ONLY clean description - NO raw tool names) */}
        {!isUser && message.toolChips && message.toolChips.length > 0 && (
          <div className="flex flex-col gap-2 mb-2 w-full">
            {message.toolChips.map((chip) => {
              const isRunning = chip.status === "running";
              return (
                <div
                  key={chip.id}
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs w-fit transition-all ${
                    isRunning
                      ? "bg-indigo-500/15 border-indigo-500/35 text-indigo-300 shadow-sm shadow-indigo-500/10"
                      : "bg-emerald-500/10 border-emerald-500/25 text-emerald-300"
                  }`}
                >
                  {isRunning ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                  ) : (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  )}

                  {/* Clean Descriptive Operation Label */}
                  <span className="text-gray-200 text-xs font-medium">
                    {chip.label}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {/* Message Text Bubble */}
        <div
          className={`p-4 rounded-2xl text-[14.5px] leading-relaxed break-words shadow-sm ${
            isUser
              ? "bg-gradient-to-r from-indigo-600 to-indigo-500 text-white rounded-tr-none shadow-md font-medium"
              : "bg-[#161F30] border border-white/10 text-gray-100 rounded-tl-none shadow-sm"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="markdown-prose text-gray-100">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-xl font-extrabold text-white mt-4 mb-2 tracking-tight">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-lg font-bold text-white mt-3.5 mb-2 border-b border-white/10 pb-1.5">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-base font-bold text-indigo-300 mt-3 mb-1.5 flex items-center gap-1.5">
                      {children}
                    </h3>
                  ),
                  h4: ({ children }) => (
                    <h4 className="text-sm font-bold text-gray-200 mt-2.5 mb-1">
                      {children}
                    </h4>
                  ),
                  p: ({ children }) => (
                    <p className="mb-3 leading-relaxed text-gray-200 last:mb-0 text-[14.5px]">
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-outside ml-5 space-y-1.5 my-3 text-gray-200">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-outside ml-5 space-y-2 my-3 text-gray-200">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => (
                    <li className="leading-relaxed pl-1 text-[14px]">
                      {children}
                    </li>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-bold text-white tracking-wide">
                      {children}
                    </strong>
                  ),
                  em: ({ children }) => (
                    <em className="italic text-indigo-200">{children}</em>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-indigo-500 pl-3.5 py-1.5 my-3 bg-indigo-500/10 rounded-r-lg text-gray-300 text-sm italic">
                      {children}
                    </blockquote>
                  ),
                  code: ({ children }) => (
                    <code className="font-mono text-[12.5px] bg-black/40 px-1.5 py-0.5 rounded border border-white/10 text-indigo-300 font-semibold">
                      {children}
                    </code>
                  ),
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-3.5 rounded-xl border border-white/10 bg-[#0c1424] shadow-md">
                      <table className="w-full text-left text-xs border-collapse">
                        {children}
                      </table>
                    </div>
                  ),
                  thead: ({ children }) => (
                    <thead className="bg-[#1e293b] text-indigo-200 border-b border-white/10 font-bold uppercase text-[11px] tracking-wider">
                      {children}
                    </thead>
                  ),
                  th: ({ children }) => (
                    <th className="p-3 font-semibold text-indigo-200 border-r border-white/5 last:border-r-0">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="p-3 border-b border-white/5 border-r border-white/5 last:border-r-0 text-gray-200">
                      {children}
                    </td>
                  ),
                  tr: ({ children }) => (
                    <tr className="hover:bg-white/[0.02] transition-colors last:border-b-0">
                      {children}
                    </tr>
                  ),
                  hr: () => <hr className="border-white/10 my-4" />,
                }}
              >
                {message.content}
              </ReactMarkdown>

              {message.isStreaming && (
                <span className="inline-block w-2 h-4 ml-1 bg-indigo-400 animate-pulse align-middle rounded-sm" />
              )}
            </div>
          )}
        </div>

        {/* Sequential Delivery Addresses Cards with Action Buttons */}
        {!isUser && !message.isStreaming && (addresses.length > 0 || message.content.toLowerCase().includes("saved delivery address")) && (
          <div className="w-full mt-2 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-300 uppercase tracking-wider">
                <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                Select Delivery Address
              </div>
              <button
                type="button"
                onClick={() => setShowAddForm((v) => !v)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-200 hover:text-white transition-all shadow-sm active:scale-95"
              >
                <Plus className="w-3.5 h-3.5" />
                {showAddForm ? "Close Form" : "+ Add New Address"}
              </button>
            </div>

            {/* Address Cards Grid */}
            {addresses.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full">
                {addresses.map((addr, idx) => (
                  <div
                    key={addr.id || idx}
                    className="p-3.5 rounded-xl border border-white/10 bg-[#162032] hover:border-indigo-500/40 transition-all flex flex-col justify-between gap-3 shadow-md group"
                  >
                    <div>
                      {/* Address Header */}
                      <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2.5">
                        <span className="font-semibold text-white text-xs flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 inline-flex items-center justify-center text-[11px] font-bold">
                            {idx + 1}
                          </span>
                          {addr.title || `Address #${idx + 1}`}
                        </span>
                        {addr.is_default && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            Default
                          </span>
                        )}
                      </div>

                      {/* Structured Address Table */}
                      <table className="w-full text-xs text-left">
                        <tbody>
                          <tr className="border-b border-white/5">
                            <td className="py-1 text-gray-400 font-medium w-20">Recipient:</td>
                            <td className="py-1 text-gray-100 font-semibold">{addr.recipient_name}</td>
                          </tr>
                          <tr className="border-b border-white/5">
                            <td className="py-1 text-gray-400 font-medium align-top">Address:</td>
                            <td className="py-1 text-gray-300 leading-snug">{addr.address}</td>
                          </tr>
                          <tr>
                            <td className="py-1 text-gray-400 font-medium">Phone:</td>
                            <td className="py-1 text-indigo-300 font-mono font-medium">{addr.phone}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    {/* Deliver to this Address Button */}
                    <button
                      type="button"
                      onClick={() =>
                        onSendQuery(
                          `Please deliver to Address ${idx + 1}: ${addr.recipient_name}, ${addr.address} (Phone: ${addr.phone})`
                        )
                      }
                      className="w-full mt-1 py-2 px-3 rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-medium text-xs flex items-center justify-center gap-1.5 shadow-md shadow-indigo-600/25 active:scale-[0.98] transition-all"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Deliver to this Address
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Interactive Add New Address Form */}
            {showAddForm && (
              <form
                onSubmit={handleFormSubmit}
                className="p-4 rounded-xl border border-indigo-500/40 bg-[#0f172a] shadow-xl animate-fadeIn mt-1"
              >
                <div className="flex items-center justify-between border-b border-white/10 pb-2.5 mb-3">
                  <div className="flex items-center gap-2 text-sm font-semibold text-white">
                    <Plus className="w-4 h-4 text-indigo-400" />
                    Enter New Delivery Address Details
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {formError && (
                  <div className="mb-3 p-2 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium">
                    {formError}
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  {/* Recipient Name */}
                  <div>
                    <label className="block text-gray-300 font-medium mb-1">
                      Recipient Full Name *
                    </label>
                    <input
                      type="text"
                      name="recipient_name"
                      value={formData.recipient_name}
                      onChange={handleFormChange}
                      placeholder="e.g. Raghava Reddy"
                      className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  {/* Phone Number */}
                  <div>
                    <label className="block text-gray-300 font-medium mb-1">
                      Phone Number *
                    </label>
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleFormChange}
                      placeholder="e.g. 9876543210"
                      className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 font-mono"
                    />
                  </div>

                  {/* Street Address */}
                  <div className="sm:col-span-2">
                    <label className="block text-gray-300 font-medium mb-1">
                      Street Address / House No. / Area *
                    </label>
                    <input
                      type="text"
                      name="address_line"
                      value={formData.address_line}
                      onChange={handleFormChange}
                      placeholder="e.g. Flat 402, Sunshine Apartments, Main Road"
                      className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  {/* City */}
                  <div>
                    <label className="block text-gray-300 font-medium mb-1">
                      City / Town
                    </label>
                    <input
                      type="text"
                      name="city"
                      value={formData.city}
                      onChange={handleFormChange}
                      placeholder="e.g. Vinukonda"
                      className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  {/* State */}
                  <div>
                    <label className="block text-gray-300 font-medium mb-1">
                      State
                    </label>
                    <input
                      type="text"
                      name="state"
                      value={formData.state}
                      onChange={handleFormChange}
                      placeholder="e.g. Andhra Pradesh"
                      className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  {/* Pincode */}
                  <div>
                    <label className="block text-gray-300 font-medium mb-1">
                      Pincode *
                    </label>
                    <input
                      type="text"
                      name="pincode"
                      value={formData.pincode}
                      onChange={handleFormChange}
                      placeholder="e.g. 522646"
                      className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 font-mono"
                    />
                  </div>

                  {/* Label / Type */}
                  <div>
                    <label className="block text-gray-300 font-medium mb-1">
                      Address Label
                    </label>
                    <select
                      name="title"
                      value={formData.title}
                      onChange={handleFormChange}
                      className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="Home">Home</option>
                      <option value="Office">Office</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2.5 mt-4 pt-3 border-t border-white/10">
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-white/5 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-indigo-600/30 active:scale-95 transition"
                  >
                    <Send className="w-3.5 h-3.5" />
                    Submit & Deliver to This Address
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {/* Quick Follow-Up Chips */}
        {!isUser && message.followups && message.followups.length > 0 && !message.isStreaming && (
          <div className="flex flex-wrap gap-2 mt-1">
            {message.followups.map((f, i) => (
              <button
                key={i}
                onClick={() => onSendQuery(f)}
                className="px-3 py-1 rounded-full bg-white/5 hover:bg-indigo-500/15 border border-white/10 hover:border-indigo-500/40 text-xs text-gray-300 hover:text-indigo-200 transition"
              >
                {f}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

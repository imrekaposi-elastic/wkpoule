import { describe, expect, it } from "vitest";
import { funCommentText } from "./funCommentText";
import type { FunComment } from "../types";

const sample: FunComment = {
  style: "lineker",
  comment_text: "English text",
  comment_text_de: "German text",
  comment_text_it: "Italian text",
  comment_text_es: "Spanish text",
};

describe("funCommentText", () => {
  it("returns Italian and Spanish without falling back to German", () => {
    expect(funCommentText(sample, "it")).toBe("Italian text");
    expect(funCommentText(sample, "es")).toBe("Spanish text");
  });

  it("falls back to English when locale column is missing", () => {
    const minimal = { style: "lineker", comment_text: "English only" };
    expect(funCommentText(minimal, "it")).toBe("English only");
  });
});

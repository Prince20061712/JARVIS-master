"use client";
import { jsx as f, jsxs as z, Fragment as D } from "react/jsx-runtime";
import { forwardRef as U, useRef as F, useState as l, useEffect as H } from "react";
import { Application as I } from "@splinetool/runtime";
import P from "./ParentSize.js";
const G = U(
  ({
    scene: s,
    style: u,
    onSplineMouseDown: p,
    onSplineMouseUp: b,
    onSplineMouseHover: d,
    onSplineKeyDown: v,
    onSplineKeyUp: w,
    onSplineStart: y,
    onSplineLookAt: h,
    onSplineFollow: S,
    onSplineScroll: k,
    onLoad: r,
    renderOnDemand: E = !0,
    wasmPath: g,
    children: x,
    ...A
  }, R) => {
    const o = F(null), [c, a] = l(!0), [i, j] = l();
    if (i)
      throw i;
    return H(() => {
      a(!0);
      let e;
      const m = [
        {
          name: "mouseDown",
          cb: p
        },
        {
          name: "mouseUp",
          cb: b
        },
        {
          name: "mouseHover",
          cb: d
        },
        {
          name: "keyDown",
          cb: v
        },
        {
          name: "keyUp",
          cb: w
        },
        {
          name: "start",
          cb: y
        },
        {
          name: "lookAt",
          cb: h
        },
        {
          name: "follow",
          cb: S
        },
        {
          name: "scroll",
          cb: k
        }
      ];
      if (o.current) {
        e = new I(o.current, {
          renderOnDemand: E,
          wasmPath: g
        });
        async function t() {
          await e.load(s);
          for (let n of m)
            n.cb && e.addEventListener(n.name, n.cb);
          a(!1), r == null || r(e);
        }
        t().catch((n) => {
          j(n);
        });
      }
      return () => {
        for (let t of m)
          t.cb && e.removeEventListener(t.name, t.cb);
        e.dispose();
      };
    }, [s]), /* @__PURE__ */ f(
      P,
      {
        ref: R,
        parentSizeStyles: { overflow: "hidden", ...u },
        debounceTime: 50,
        ...A,
        children: () => /* @__PURE__ */ z(D, { children: [
          c && x,
          /* @__PURE__ */ f(
            "canvas",
            {
              ref: o,
              style: {
                display: c ? "none" : "block"
              }
            }
          )
        ] })
      }
    );
  }
);
export {
  G as default
};

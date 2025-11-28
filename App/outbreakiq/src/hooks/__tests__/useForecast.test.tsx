import { renderHook, act } from "@testing-library/react";
import { useForecast } from "../../hooks/useForecast";
import { outbreakAPI } from "../../services/api";

jest.mock("../../services/api", () => {
  return {
    outbreakAPI: {
      climate: {
        getForecast: jest.fn(() =>
          Promise.resolve({
            data: {
              data: {
                region: "Lagos",
                temperature: [
                  { date: "2025-11-14", value: 30 },
                  { date: "2025-11-15", value: 31 },
                ],
                rainfall: [
                  { date: "2025-11-14", value: 10 },
                  { date: "2025-11-15", value: 12 },
                ],
              },
            },
          })
        ),
      },
    },
  };
});

describe("useForecast", () => {
  it("loads forecast series", async () => {
    const { result } = renderHook(() => useForecast("Lagos", 7));
    expect(result.current.loading).toBe(true);
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0));
    });
    expect(outbreakAPI.climate.getForecast).toHaveBeenCalledWith("Lagos", 7);
    expect(result.current.loading).toBe(false);
    expect(result.current.tempData.length).toBeGreaterThan(0);
    expect(result.current.rainData.length).toBeGreaterThan(0);
  });
});
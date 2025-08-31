import plotly.graph_objs as go
import pandas as pd

def plot_candlestick(hist: pd.DataFrame, symbol: str):
    fig = go.Figure(data=[
        go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name='Candles'
        )
    ])
    fig.update_layout(title=f'📈 גרף נרות: {symbol}', xaxis_rangeslider_visible=False, height=500)
    return fig


def plot_intraday_openingbell(df: pd.DataFrame, symbol: str):
    """
    גרף 5m: נרות + SMA20/SMA200, הדגשת נר הפתיחה, וטולטיפ מותאם.
    משתמש ב-attrs ("open_idx", "signal_at_open", "reason_at_open") אם קיימים.
    """
    fig = go.Figure()

    # --- Candles + custom hovertext (ל תאימות לגרסאות ללא hovertemplate) ---
    idx = df.index
    try:
        times = pd.to_datetime(idx).strftime("%Y-%m-%d %H:%M")
    except Exception:
        times = [str(x) for x in idx]

    hovertext = [
        f"<b>{t}</b><br>"
        f"Open: {float(o):.3f}<br>"
        f"High: {float(h):.3f}<br>"
        f"Low: {float(l):.3f}<br>"
        f"Close: {float(c):.3f}"
        for t, o, h, l, c in zip(times, df["Open"], df["High"], df["Low"], df["Close"])
    ]

    fig.add_trace(go.Candlestick(
        x=idx,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="5m",
        hovertext=hovertext,
        hoverinfo="text",
    ))

    # --- SMAs ---
    if "SMA20" in df.columns:
        fig.add_trace(go.Scatter(x=idx, y=df["SMA20"], mode="lines", name="SMA20", hoverinfo="skip"))
    if "SMA200" in df.columns:
        fig.add_trace(go.Scatter(x=idx, y=df["SMA200"], mode="lines", name="SMA200", hoverinfo="skip"))

    # --- Opening bar index (מה-attrs אם יש, אחרת מהעמודה is_opening) ---
    open_idx = df.attrs.get("open_idx")
    if open_idx is None and "is_opening" in df.columns and df["is_opening"].any():
        open_idx = df.index[df["is_opening"]][0]

    # --- נתוני OPEN/Now להצגה עקבית ---
    sig_open = df.attrs.get("signal_at_open")
    reason_open = df.attrs.get("reason_at_open")
    if (sig_open is None) and (open_idx is not None) and ("signal" in df.columns):
        try:
            sig_open = df.loc[open_idx, "signal"]
        except Exception:
            pass
    if (reason_open is None) and (open_idx is not None) and ("signal_reason" in df.columns):
        try:
            reason_open = df.loc[open_idx, "signal_reason"]
        except Exception:
            pass

    sig_now = None
    if "signal" in df.columns and len(df) > 0:
        try:
            sig_now = str(df["signal"].iloc[-1])
        except Exception:
            pass

    # --- Opening bar highlight + signal marker ---
    if open_idx is not None and open_idx in df.index:
        try:
            x0 = pd.to_datetime(open_idx) - pd.Timedelta(minutes=2, seconds=30)
            x1 = pd.to_datetime(open_idx) + pd.Timedelta(minutes=2, seconds=30)
            fig.add_vrect(x0=x0, x1=x1, opacity=0.15, line_width=0)
        except Exception:
            pass

        try:
            y_mark = float(df.loc[open_idx, "Open"])
        except Exception:
            y_mark = None

        if y_mark is not None:
            fig.add_trace(go.Scatter(
                x=[open_idx], y=[y_mark],
                mode="markers+text",
                name="Signal@Open",
                text=[str(sig_open) if sig_open is not None else ""],
                textposition="top center",
                hovertext=[f"{symbol} — Open: {sig_open or 'N/A'}<br>{reason_open or ''}"],
                hoverinfo="text",
            ))

    # --- Annotation מסכם (Open vs Now) ---
    if len(df) > 0:
        try:
            ann_text = f"{symbol} — Open: {sig_open or 'N/A'}"
            if sig_now and sig_open and sig_now != sig_open:
                ann_text += f"  |  Now: {sig_now}"
            fig.add_annotation(
                x=df.index[-1],
                y=float(df['Close'].iloc[-1]),
                text=ann_text,
                showarrow=False,
                align="right"
            )
        except Exception:
            pass

    fig.update_layout(
        title=f"⚡ Intraday 5m — {symbol}",
        xaxis_rangeslider_visible=False,
        height=520,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig

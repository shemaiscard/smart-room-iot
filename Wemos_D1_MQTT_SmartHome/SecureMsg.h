// SecureMsg.h - sealed MQTT payloads, the same format as secure_msg.py:
//   <timestamp ms>|<hex of nonce (12 bytes) + ciphertext + tag (16 bytes)>
// AES-256-GCM with "<topic>|<timestamp>" as associated data. The key is
// SHA-256("smart-room-v2|" + shared secret). Plain C buffers only, so the same
// file also compiles on a PC for testing against the dashboard's Python code.
#pragma once
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <bearssl/bearssl.h>

class SecureMsg {
 public:
  void begin(const char* secret) {
    br_sha256_context h;
    br_sha256_init(&h);
    br_sha256_update(&h, "smart-room-v2|", 14);
    br_sha256_update(&h, secret, strlen(secret));
    br_sha256_out(&h, key_);
  }

  // Writes the sealed payload to out (needs 22 + 2 * (strlen(body) + 28) bytes).
  // Returns false if out is too small.
  bool seal(const char* topic, const char* body, unsigned long long ts, const uint8_t nonce[12],
            char* out, size_t out_size) {
    size_t n = strlen(body);
    if (n > MAX_BODY || out_size < 22 + 2 * (n + 28)) return false;
    uint8_t blob[12 + MAX_BODY + 16];
    memcpy(blob, nonce, 12);
    memcpy(blob + 12, body, n);
    char ts_str[21];
    u64_to_str(ts, ts_str);
    crypt(topic, ts_str, blob, blob + 12, n, true);
    int len = snprintf(out, out_size, "%s|", ts_str);
    to_hex(blob, 12 + n + 16, out + len);
    return true;
  }

  // Opens a sealed payload. Returns the body length (body is NUL-terminated),
  // or -1 if the payload is malformed or not authentic. *ts receives the timestamp.
  int open(const char* topic, const char* payload, char* body, size_t body_size, unsigned long long* ts) {
    const char* bar = strchr(payload, '|');
    if (!bar || bar == payload || bar - payload > 20) return -1;
    char ts_str[21];
    memcpy(ts_str, payload, bar - payload);
    ts_str[bar - payload] = '\0';
    for (const char* p = ts_str; *p; p++) if (*p < '0' || *p > '9') return -1;
    const char* hex = bar + 1;
    size_t hex_len = strlen(hex);
    if (hex_len % 2 || hex_len < 2 * 28 || hex_len > 2 * (12 + MAX_BODY + 16)) return -1;
    uint8_t blob[12 + MAX_BODY + 16];
    size_t blob_len = hex_len / 2;
    if (!from_hex(hex, hex_len, blob)) return -1;
    size_t n = blob_len - 28;
    if (n + 1 > body_size) return -1;
    if (!crypt(topic, ts_str, blob, blob + 12, n, false)) return -1;
    memcpy(body, blob + 12, n);
    body[n] = '\0';
    *ts = strtoull(ts_str, nullptr, 10);
    return (int)n;
  }

 private:
  static const size_t MAX_BODY = 96;
  uint8_t key_[32];

  // GCM over data in place; the tag follows the data. Returns false on a bad tag.
  bool crypt(const char* topic, const char* ts_str, const uint8_t* nonce, uint8_t* data, size_t n, bool encrypt) {
    br_aes_ct_ctr_keys bc;
    br_gcm_context gc;
    br_aes_ct_ctr_init(&bc, key_, 32);
    br_gcm_init(&gc, &bc.vtable, br_ghash_ctmul32);
    br_gcm_reset(&gc, nonce, 12);
    br_gcm_aad_inject(&gc, topic, strlen(topic));
    br_gcm_aad_inject(&gc, "|", 1);
    br_gcm_aad_inject(&gc, ts_str, strlen(ts_str));
    br_gcm_flip(&gc);
    if (encrypt) {
      br_gcm_run(&gc, 1, data, n);
      br_gcm_get_tag(&gc, data + n);
      return true;
    }
    br_gcm_run(&gc, 0, data, n);
    return br_gcm_check_tag(&gc, data + n) == 1;
  }

  static void u64_to_str(unsigned long long v, char out[21]) {
    char buf[21];
    int i = 20;
    buf[i] = '\0';
    do { buf[--i] = '0' + (v % 10); v /= 10; } while (v > 0);
    strcpy(out, &buf[i]);
  }

  static void to_hex(const uint8_t* in, size_t n, char* out) {
    static const char digits[] = "0123456789abcdef";
    for (size_t i = 0; i < n; i++) { out[2 * i] = digits[in[i] >> 4]; out[2 * i + 1] = digits[in[i] & 15]; }
    out[2 * n] = '\0';
  }

  static int nibble(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
  }

  static bool from_hex(const char* hex, size_t hex_len, uint8_t* out) {
    for (size_t i = 0; i < hex_len; i += 2) {
      int hi = nibble(hex[i]), lo = nibble(hex[i + 1]);
      if (hi < 0 || lo < 0) return false;
      out[i / 2] = (uint8_t)(hi << 4 | lo);
    }
    return true;
  }
};

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <limits.h>
#include <printf.h>

#define MAX_METADATA 10
#define MAX_METADATA_KEY_SIZE 50
#define MAX_METADATA_VALUE_SIZE 100
#define MAX_STREAM_SIZE 250
#define MAX_STREAMS 512
#define FONT_SIZE 12
#define START_X 64
#define START_Y 750
#define Y_OFFSET 20
#define MAX_STR 2048

typedef struct Stream {
    unsigned short size;
    char* data;
    float x;
    float y;
    struct Stream* next;
} Stream;

typedef struct {
    char key[MAX_METADATA_KEY_SIZE];
    char value[MAX_METADATA_VALUE_SIZE];
} Metadata;

typedef struct {
    Stream* head;
    int stream_count;
    Metadata metadata[MAX_METADATA];
    int metadata_count;
} PDF;


PDF* create_pdf() {
    PDF* pdf = (PDF*)calloc(1, sizeof(PDF));
    pdf->head = NULL;
    pdf->stream_count = 0;
    pdf->metadata_count = 0;
    return pdf;
}

void add_metadata(PDF* pdf, const char* key, const char* value) {
    if (pdf->metadata_count >= MAX_METADATA) {
        printf("Error: Maximum number of metadata entries reached.\n");
        return;
    }

    Metadata* meta = &pdf->metadata[pdf->metadata_count];
    strncpy(meta->key, key, MAX_METADATA_KEY_SIZE - 1);
    meta->key[MAX_METADATA_KEY_SIZE - 1] = '\0';
    strncpy(meta->value, value, MAX_METADATA_VALUE_SIZE - 1);
    meta->value[MAX_METADATA_VALUE_SIZE - 1] = '\0';

    pdf->metadata_count++;
    printf("Metadata added successfully: %s = %s\n", key, value);
}

void remove_metadata(PDF* pdf, const char* key) {
    for (int i = 0; i < pdf->metadata_count; i++) {
        if (strcmp(pdf->metadata[i].key, key) == 0) {
            for (int j = i; j < pdf->metadata_count - 1; j++) {
                pdf->metadata[j] = pdf->metadata[j + 1];
            }
            pdf->metadata_count--;
            printf("Metadata removed successfully: %s\n", key);
            return;
        }
    }
    printf("Error: Metadata key not found: %s\n", key);
}

void add_stream(PDF* pdf, const char* text) {
    if (pdf->stream_count >= MAX_STREAMS) {
        printf("Error: Maximum number of streams reached.\n");
        return;
    }

    Stream* new_stream = (Stream*)malloc(sizeof(Stream));
    if (new_stream == NULL) {
        printf("Error: Memory allocation failed for stream structure.\n");
        return;
    }

    new_stream->data = strndup(text, MAX_STREAM_SIZE - 1);
    if (new_stream->data == NULL) {
        printf("Error: Memory allocation failed for stream data.\n");
        free(new_stream);
        return;
    }

    new_stream->size = strlen(new_stream->data);
    new_stream->x = START_X;
    new_stream->y = START_Y - (pdf->stream_count * Y_OFFSET);
    new_stream->next = NULL;

    if (pdf->head == NULL) {
        pdf->head = new_stream;
    } else {
        Stream* current = pdf->head;
        while (current->next != NULL) {
            current = current->next;
        }
        current->next = new_stream;
    }

    pdf->stream_count++;
    printf("Stream added successfully.\n");
}

void modify_stream(PDF* pdf, int index, const char* new_text) {
    if (index < 0 || index >= pdf->stream_count) {
        printf("Error: Invalid stream index.\n");
        return;
    }

    Stream* current = pdf->head;
    for (int i = 0; i < index; i++) {
        current = current->next;
    }

    strcpy(current->data, new_text);
    current->size = strlen(new_text);

    printf("Stream modified successfully.\n");
}

void remove_stream(PDF* pdf, int index) {
    if (index < 0 || index >= pdf->stream_count) {
        printf("Error: Invalid stream index.\n");
        return;
    }

    Stream* current = pdf->head;
    Stream* previous = NULL;

    if (index == 0) {
        pdf->head = current->next;
    } else {
        for (int i = 0; i < index; i++) {
            previous = current;
            current = current->next;
        }
        previous->next = current->next;
    }

    free(current->data);
    free(current);

    pdf->stream_count--;

    // Adjust y-coordinates of subsequent streams
    current = (index == 0) ? pdf->head : previous->next;
    while (current != NULL) {
        current->y += Y_OFFSET;
        current = current->next;
    }

    printf("Stream removed successfully.\n");
}

void generate_pdf(PDF* pdf, const char* filename) {
    FILE *file;
    int writing_to_stdout = 0;

    if (filename == NULL || strcmp(filename, "stdout") == 0) {
        file = stdout;
        writing_to_stdout = 1;
    } else {
        file = fopen(filename, "wb");
        if (!file) {
            printf("Error: Unable to create file '%s'.\n", filename);
            return;
        }
    }

    // PDF Header
    fprintf(file, "%%PDF-1.3\n%%\xE2\xE3\xCF\xD3\n");

    // Object 1: Info dictionary (Metadata)
    long obj1_offset = ftell(file);
    fprintf(file, "1 0 obj\n<<\n");
    for (int i = 0; i < pdf->metadata_count; i++) {
        fprintf(file, " /%s (%s)\n", pdf->metadata[i].key, pdf->metadata[i].value);
    }
    fprintf(file, ">>\nendobj\n");

    // Object 2: Catalog
    long obj2_offset = ftell(file);
    fprintf(file, "2 0 obj\n<<\n /Type /Catalog\n /Pages 3 0 R\n>>\nendobj\n");

    // Object 3: Pages
    long obj3_offset = ftell(file);
    fprintf(file, "3 0 obj\n<<\n /Type /Pages\n /Kids [4 0 R]\n /Count 1\n>>\nendobj\n");

    // Object 4: Page
    long obj4_offset = ftell(file);
    fprintf(file, "4 0 obj\n<<\n /Type /Page\n /Parent 3 0 R\n /MediaBox [0 0 595.275574 841.889771]\n /Resources <<\n /Font << /F1 5 0 R >>\n >>\n /Contents [\n");

    // Write stream references
    int stream_index = 6;
    Stream* current = pdf->head;
    while (current != NULL) {
        fprintf(file, " %d 0 R\n", stream_index++);
        current = current->next;
    }
    fprintf(file, " ]\n>>\nendobj\n");

    // Object 5: Font
    long obj5_offset = ftell(file);
    fprintf(file, "5 0 obj\n<<\n /Type /Font\n /Subtype /Type1\n /BaseFont /Times-Roman\n /Encoding /WinAnsiEncoding\n>>\nendobj\n");

    // Write streams
    long stream_offsets[MAX_STREAMS];
    stream_index = 0;
    current = pdf->head;
    while (current != NULL) {
        stream_offsets[stream_index] = ftell(file);
        int size = snprintf(NULL, 0,
        "BT /F1 %.2f Tf 0 0 0 rg %.2f %.2f Td (%s) Tj ET", 
        (float)FONT_SIZE, current->x, current->y, current->data);
        fprintf(file, "%d 0 obj\n<< /Length %zu >>\nstream\n", stream_index + 6, size);
        fprintf(file, "BT /F1 %.2f Tf 0 0 0 rg %.2f %.2f Td (",  (float)FONT_SIZE, current->x, current->y);
        fwrite(current->data, 1, current->size, file);
        fprintf(file, ") Tj ET");
        fprintf(file, "\nendstream\nendobj\n");
        current = current->next;
        stream_index++;
    }

    // Write xref
    long xref_offset = ftell(file);
    fprintf(file, "xref\n");
    fprintf(file, "0 %d\n", pdf->stream_count + 6);
    fprintf(file, "0000000000 65535 f \n");
    fprintf(file, "%010ld 00000 n \n", obj1_offset);
    fprintf(file, "%010ld 00000 n \n", obj2_offset);
    fprintf(file, "%010ld 00000 n \n", obj3_offset);
    fprintf(file, "%010ld 00000 n \n", obj4_offset);
    fprintf(file, "%010ld 00000 n \n", obj5_offset);
    for (int i = 0; i < pdf->stream_count; i++) {
        fprintf(file, "%010ld 00000 n \n", stream_offsets[i]);
    }

    // Write trailer
    fprintf(file, "trailer\n<<\n/Size %d\n/Root 2 0 R\n/Info 1 0 R\n>>\n", pdf->stream_count + 6);
    fprintf(file, "startxref\n%ld\n%%%%EOF\n", xref_offset);

    if (!writing_to_stdout) {
        fclose(file);
    }
    printf("PDF generated successfully.\n");
}

void free_pdf(PDF* pdf) {
    Stream* current = pdf->head;
    while (current != NULL) {
        Stream* next = current->next;
        free(current->data);
        free(current);
        current = next;
    }
    free(pdf);
}

void display_pdf_state(PDF* pdf) {
    printf("\n--- Current PDF State ---\n\n");
    
    printf("Metadata entries: %d\n", pdf->metadata_count);
    for (int i = 0; i < pdf->metadata_count; i++) {
        printf("  %s: %s\n", pdf->metadata[i].key, pdf->metadata[i].value);
    }
    
    printf("Stream count: %d\n", pdf->stream_count);
    Stream* current = pdf->head;
    int index = 0;
    while (current != NULL) {
        printf("  Stream %d: %s\n", index++, current->data);
        current = current->next;
    }
    
    printf("\n--- END ---\n");
}


int parse_int(const char* str, int* result) {
    char* endptr;
    errno = 0;
    long val = strtol(str, &endptr, 10);

    if ((errno == ERANGE && (val == LONG_MAX || val == LONG_MIN))
        || (errno != 0 && val == 0)) {
        return 0;  // Error occurred
    }
    if (endptr == str) {
        return 0;  // No digits were found
    }
    if (*endptr != '\0') {
        return 0;  // String contains invalid characters
    }
    if (val > INT_MAX || val < INT_MIN) {
        return 0;  // Value out of range for int
    }
    *result = (int)val;
    return 1;  // Successful conversion
}

char* extract_quoted_string(char* str) {
    char* start = strchr(str, '"');
    if (start == NULL) return NULL;
    char* end = strchr(start + 1, '"');
    if (end == NULL) return NULL;
    *end = '\0';
    return start + 1;
}

void print_help() {
    printf("\n--- PDF Manager Commands ---\n");
    printf("1500 \"<key>\" \"<value>\" : Add metadata\n");
    printf("1501 \"<key>\" : Remove metadata\n");
    printf("1502 \"<text>\" : Add stream\n");
    printf("1503 \"<index>\" : Remove stream\n");
    printf("1504 \"<filename>\" : Generate PDF\n");
    printf("1505 : Display current PDF state\n");
    printf("1506 : Display this help message\n");
    printf("1507 : Exit\n");
    printf("1508 \"<index>\" \"<new_text>\" : Modify stream\n");
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);

    PDF* pdf = create_pdf();
    char input[MAX_STR];
    int op_code;

    while (1) {
        if (fgets(input, sizeof(input), stdin) == NULL) {
            break;
        }

        input[strcspn(input, "\n")] = 0;


        if (sscanf(input, "%d", &op_code) != 1) {
            printf("Error: Invalid operation code. Type 1506 for help.\n");
            fflush(stdout);
            continue;
        }
        char* rest = strchr(input, ' ');
        if (rest != NULL) {
            rest++;
        }
        else {
            if(op_code < 1504 || op_code >=1508  )
                {
                    printf("Error: Invalid operation format. Type 1506 for help.\n");
                    fflush(stdout);
                    continue;
                }
        }
    
        switch (op_code) {
            case 1500: {
                char* key = extract_quoted_string(rest);
                if (key == NULL) {
                    printf("Error: Invalid key format.\n");
                    break;
                }
                char* value = extract_quoted_string(strchr(key, '\0') + 1);
                if (value == NULL) {
                    printf("Error: Usage: 1500 \"<key>\" \"<value>\"\n");
                    break;
                }
                add_metadata(pdf, key, value);
                break;
            }
            case 1501: {
                char* key = extract_quoted_string(rest);
                if (key == NULL) {
                    printf("Error: Usage: 1501 \"<key>\"\n");
                    break;
                }
                remove_metadata(pdf, key);
                break;
            }
            case 1502: {
                char* text = extract_quoted_string(rest);
                if (text == NULL) {
                    printf("Error: Usage: 1502 \"<text>\"\n");
                    break;
                }
                add_stream(pdf, text);
                break;
            }
            case 1503: {
                char* index_str = extract_quoted_string(rest);
                if (index_str == NULL) {
                    printf("Error: Usage: 1503 \"<index>\"\n");
                    break;
                }
                int index;
                if (!parse_int(index_str, &index)) {
                    printf("Error: Invalid index. Please provide a valid integer.\n");
                    break;
                }
                remove_stream(pdf, index);
                break;
            }
            case 1504: {
                char* filename = "stdout";
                if (filename == NULL) {
                    printf("Error: Usage: 1504 \"<filename>\"\n");
                    break;
                }
                generate_pdf(pdf, filename);
                break;
            }
            case 1505:
                display_pdf_state(pdf);
                break;
            case 1506:
                print_help();
                break;
            case 1507:
                free_pdf(pdf);
                printf("Exiting program. Goodbye!\n");
                return 0;
            case 1508: {
                char* index_str = extract_quoted_string(rest);
                if (index_str == NULL) {
                    printf("Error: Invalid index format.\n");
                    break;
                }
                int index;
                if (!parse_int(index_str, &index)) {
                    printf("Error: Invalid index. Please provide a valid integer.\n");
                    break;
                }
                char* new_text_start = strchr(index_str, '\0') + 1;
                while (*new_text_start == ' ') {
                    new_text_start++;
                }
                char* new_text = extract_quoted_string(new_text_start - 1); //mod
                if (new_text == NULL) {
                    printf("Error: Usage: 1508 \"<index>\" \"<new_text>\"\n");
                    break;
                }
                modify_stream(pdf, index, new_text);
                break;
            }
            default:
                printf("Error: Invalid operation code. Type 1506 for help.\n");
        }
    }
    return 0;
}
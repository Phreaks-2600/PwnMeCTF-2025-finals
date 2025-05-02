#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libtasn1.h>

#define ASN1_SMALL_VALUE_SIZE 16
#define SIZE_BUFF 0x400
#define DEFAULT_SIZE 0x100

typedef struct asn1_node_st asn1_node_st;
typedef asn1_node_st *asn1_node;
typedef const asn1_node_st *asn1_node_const;

struct asn1_node_array_st
{
  asn1_node *nodes;
  size_t size;
};

struct asn1_node_st
{
  /* public fields: */
  char name[ASN1_MAX_NAME_SIZE + 1];	/* Node name */
  unsigned int name_hash;
  unsigned int type;		/* Node type */
  unsigned char *value;		/* Node value */
  int value_len;
  asn1_node down;		/* Pointer to the son node */
  asn1_node right;		/* Pointer to the brother node */
  asn1_node left;		/* Pointer to the next list element */
  /* private fields: */
  unsigned char small_value[ASN1_SMALL_VALUE_SIZE];	/* For small values */
  asn1_node parent;		/* Pointer to the parent node */
  struct asn1_node_array_st numbered_children;	/* Array of unnamed child nodes for caching */

  /* values used during decoding/coding */
  int tmp_ival;
  unsigned start;		/* the start of the DER sequence - if decoded */
  unsigned end;			/* the end of the DER sequence - if decoded */
};

/*
		GLOBALS
*/

asn1_node structure_node, main_elem;
int chunks;

/*
		FUNCTIONS
*/

void prelude(){
		setvbuf(stdin, NULL, _IONBF, 0);
		setvbuf(stdout, NULL, _IONBF, 0);
}

int read_num(){
	char buffer[32];
	int res;
	fgets(buffer, sizeof(buffer), stdin);
	res = strtol(buffer, NULL, 0);
	return res;
}

void read_string(char *buffer, int size){
	int len;
	fgets(buffer, size, stdin);

	len = strlen(buffer);
	if (len && buffer[len - 1] == '\n'){
		buffer[len - 1] = 0;
	}
}

void menu(){
	puts("Here are the choices available:");
	puts("1. Create ASN1 node structure.");
	puts("2. Dump asn1 node structure.");
	puts("3. Edit asn1 node structure.");
	puts("4. Print node structure.");
	puts("5. Create an element.");
	puts("6. Delete an element.");
	puts("7. Read an element value.");
	puts("8. Write an element value.");
	puts("9. Take a break, alloc a chunk.");
	puts("10. Exit.");
	puts("> ");
}

void read_node(){
	char buffer[SIZE_BUFF];
	char errorDescription[ASN1_MAX_ERROR_DESCRIPTION_SIZE];
	int ret;
	FILE *f = fopen("./node.asn1", "wb");

	puts("What's your node:");
	memset(buffer, 0, SIZE_BUFF);
	read(0, buffer, SIZE_BUFF);

	fwrite(buffer, strlen(buffer), 1, f);
	fclose(f);

	structure_node = NULL;
	ret = asn1_parser2tree("./node.asn1", &structure_node, errorDescription);
}

void dumps_node(){
	if (!main_elem)
		return;

	puts("Here is the node:");
	write(1, main_elem, sizeof(struct asn1_node_st));
}

void edits_node(){
	if (!main_elem)
		return;

	puts("Enter the new node:");
	read(0, main_elem, sizeof(struct asn1_node_st));
}

void prints_node(){
	char name[DEFAULT_SIZE];
	if (!structure_node)
		return;

	puts("What name should we print:");
	read_string(name, sizeof(name));

	asn1_print_structure(stdout, structure_node, name, ASN1_PRINT_ALL);
}

void creates_element(){
	char name[DEFAULT_SIZE];
	if (!structure_node)
		return;

	puts("Which element:");
	read_string(name, sizeof(name));

	asn1_create_element(structure_node, name, &main_elem);
}

void deletes_element(){
	char name[DEFAULT_SIZE];
	if (!main_elem)
		return;

	puts("Which element:");
	read_string(name, sizeof(name));

	asn1_delete_element(main_elem, name);
}

void read_value(){
	char name[DEFAULT_SIZE], value[DEFAULT_SIZE];
	int len, ret;
	if (!main_elem)
		return;

	memset(value, 0, sizeof(value));

	puts("Which value to read:");
	read_string(name, sizeof(name));

	len = DEFAULT_SIZE;
	ret = asn1_read_value(main_elem, name, value, &len);

	printf("Read %d bytes\n", len);
	puts(value);
}

void write_value(){
	char name[DEFAULT_SIZE];
	char *buffer;
	int size, ret;

	if (!main_elem)
		return;

	puts("Which value to write:");
	read_string(name, sizeof(name));

	puts("How long is the value:");
	size = read_num();

	if (size < 0 || size > SIZE_BUFF){
		puts("Invalid size.");
		return;
	}

	buffer = (char *)malloc(size);
	puts("Enter the value to write:");
	read(0, buffer, size);

	ret = asn1_write_value(main_elem, name, buffer, size);
}

void alloc_chunk(){
	int size;
	char *buffer;
	if (!chunks){
		puts("No chunks left.");
		return;
	}

	puts("Which size:");
	size = read_num();
	if (size < 0 || size > 0x1000){
		puts("Invalid size.");
		return;
	}

	buffer = malloc(size);
	chunks--;

	puts("Feel free to fill your chunk:");
	read(0, buffer, size);
}

int main(){
	int choice;
	chunks = 2;

	prelude();
	
	while (1){
		menu();
		choice = read_num();
		switch (choice){
		case 1:
			read_node();
			break;
		case 2:
			dumps_node();
			break;
		case 3:
			edits_node();
			break;
		case 4:
			prints_node();
			break;
		case 5:
			creates_element();
			break;
		case 6:
			deletes_element();
			break;
		case 7:
			read_value();
			break;
		case 8:
			write_value();
			break;
		case 9:
			alloc_chunk();
			break;
		case 10:
			return 0;
		}
	}
	return 0;
}
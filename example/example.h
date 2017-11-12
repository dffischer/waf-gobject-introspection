#ifndef __EXAMPLE_H__
#define __EXAMPLE_H__

#include <glib/gprintf.h>

G_BEGIN_DECLS

/**
 * example_greet:
 * @gretee: who to greet
 *
 * Emits a greeting message, directed at a given entity.
 */
void example_greet(gchar *gretee);

G_END_DECLS

#endif /* __EXAMPLE_H__ */
